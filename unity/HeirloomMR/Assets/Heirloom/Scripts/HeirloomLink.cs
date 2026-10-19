using System;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace Heirloom
{
    /// <summary>
    /// Connects to the Python brain over WebSocket.
    /// Receives: poses (moves the rig), state (for the overlay), sounds (chirps).
    /// Sends: where the user's head is, and events (gestures, voice, keys).
    /// Uses .NET's built-in ClientWebSocket (works in the Editor and on Quest). Reconnects every 2 s.
    /// </summary>
    public class HeirloomLink : MonoBehaviour
    {
        [Tooltip("In the Editor use localhost. On the Quest use your PC's IP, e.g. ws://192.168.1.20:8765")]
        public string url = "ws://localhost:8765";
        public ReachyRig rig;

        [Tooltip("Where the chirps come from. Leave empty and one is added to the robot's head.")]
        public AudioSource voice;

        [Tooltip("The user's head. Leave empty to use the headset camera. In the Editor, assign an empty object and drag it around to fake a person.")]
        public Transform userHead;
        [Tooltip("How often to tell the brain where the user is")]
        public float userSendRate = 15f;

        public bool Connected => _connected;
        public string BrainMode { get; private set; } = "";
        public string BrainExpression { get; private set; } = "";
        public float UserDistance { get; private set; } = -1f;

        [Serializable]
        class Message
        {
            public string type;
            public Channels ch;           // "pose"
            public string mode;           // "state"
            public string expression;     // "state"
            public float user_distance;   // "state", -1 = nobody
            public string name;           // "sound"
            public string wav_b64;        // "sound"
        }

        [Serializable] class UserMessage { public string type = "user"; public float[] head; }
        [Serializable] class EventMessage { public string type = "event"; public string name; }

        readonly ConcurrentQueue<string> _inbox = new ConcurrentQueue<string>();
        readonly ConcurrentQueue<string> _outbox = new ConcurrentQueue<string>();
        CancellationTokenSource _cts;
        volatile bool _connected;
        ClientWebSocket _ws;
        bool _sending;
        float _nextUserSend;

        /// <summary>Tell the brain something happened: "wave", "good", "not_now", "sleep", "wake"...</summary>
        public void SendEvent(string eventName)
        {
            _outbox.Enqueue(JsonUtility.ToJson(new EventMessage { name = eventName }));
        }

        /// <summary>Send any JSON message to the brain (used by HandStream). Dropped while disconnected.</summary>
        public void Send(string json)
        {
            if (_connected && _outbox.Count < 10) _outbox.Enqueue(json);
        }

        void OnEnable()
        {
            _cts = new CancellationTokenSource();
            _ = RunAsync(_cts.Token);
        }

        void OnDisable()
        {
            _cts?.Cancel();
            _cts = null;
        }

        void Start()
        {
            if (voice == null && rig != null && rig.head != null)
            {
                voice = rig.head.gameObject.AddComponent<AudioSource>();
                voice.playOnAwake = false;
                voice.spatialBlend = 0.8f;   // mostly 3D, so it sounds like it comes from the robot
            }
        }

        async Task RunAsync(CancellationToken ct)
        {
            bool warned = false;
            var buffer = new byte[64 * 1024];

            while (!ct.IsCancellationRequested)
            {
                using (var ws = new ClientWebSocket())
                {
                    _ws = ws;
                    try
                    {
                        await ws.ConnectAsync(new Uri(url), ct);
                        _connected = true;
                        warned = false;
                        Debug.Log("[Heirloom] Brain connected");

                        var sb = new StringBuilder();
                        while (ws.State == WebSocketState.Open && !ct.IsCancellationRequested)
                        {
                            var result = await ws.ReceiveAsync(new ArraySegment<byte>(buffer), ct);
                            if (result.MessageType == WebSocketMessageType.Close) break;
                            sb.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
                            if (result.EndOfMessage)
                            {
                                _inbox.Enqueue(sb.ToString());
                                sb.Clear();
                            }
                        }
                    }
                    catch (OperationCanceledException) { break; }
                    catch (Exception e)
                    {
                        if (!warned)   // retries every 2 s, so only say it once
                        {
                            warned = true;
                            Debug.Log($"[Heirloom] Waiting for the brain at {url} ({e.Message})");
                        }
                    }
                    finally
                    {
                        if (_connected) Debug.Log("[Heirloom] Brain disconnected");
                        _connected = false;
                        _ws = null;
                    }
                }

                try { await Task.Delay(2000, ct); }
                catch (OperationCanceledException) { break; }
            }
        }

        void Update()
        {
            // Handle everything that arrived. Only the newest pose matters, so older ones are skipped.
            Channels latestPose = null;
            while (_inbox.TryDequeue(out var raw))
            {
                var msg = JsonUtility.FromJson<Message>(raw);
                if (msg == null) continue;
                switch (msg.type)
                {
                    case "pose": latestPose = msg.ch; break;
                    case "state":
                        BrainMode = msg.mode;
                        BrainExpression = msg.expression;
                        UserDistance = msg.user_distance;
                        break;
                    case "sound": PlaySound(msg.wav_b64); break;
                }
            }
            if (latestPose != null && rig != null) rig.Apply(latestPose);

            if (!_connected) return;

            // The brain wants to know where the user is about 15 times a second.
            if (Time.time >= _nextUserSend)
            {
                _nextUserSend = Time.time + 1f / Mathf.Max(1f, userSendRate);
                var json = UserJson();
                if (json != null && _outbox.Count < 5) _outbox.Enqueue(json);
            }
            FlushOutbox();
        }

        void PlaySound(string wavB64)
        {
            if (voice == null || string.IsNullOrEmpty(wavB64)) return;
            var clip = WavUtility.FromWav(Convert.FromBase64String(wavB64), "chirp");
            if (clip != null) voice.PlayOneShot(clip);
        }

        string UserJson()
        {
            if (rig == null) return null;
            var headT = userHead != null ? userHead : (Camera.main != null ? Camera.main.transform : null);
            if (headT == null) return null;
            // User's head relative to the robot's resting head, in the robot's own axes (x right, y up, z forward).
            var rel = Quaternion.Inverse(rig.transform.rotation) * (headT.position - rig.HeadRestWorld);
            return JsonUtility.ToJson(new UserMessage { head = new[] { rel.x, rel.y, rel.z } });
        }

        // A WebSocket can only send one message at a time, so messages wait in a queue.
        async void FlushOutbox()
        {
            var ws = _ws;
            if (_sending || ws == null || ws.State != WebSocketState.Open) return;
            _sending = true;
            try
            {
                while (_outbox.TryDequeue(out var json))
                {
                    var bytes = Encoding.UTF8.GetBytes(json);
                    await ws.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
                }
            }
            catch (Exception) { /* connection dropped; the receive loop handles reconnecting */ }
            finally { _sending = false; }
        }
    }
}
