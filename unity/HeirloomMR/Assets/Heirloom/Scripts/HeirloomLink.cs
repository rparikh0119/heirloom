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
    /// Connects to the Python brain over WebSocket and forwards pose frames to the rig.
    /// Uses .NET's built-in ClientWebSocket (works in the Editor and on Quest). Reconnects every 2 s.
    /// </summary>
    public class HeirloomLink : MonoBehaviour
    {
        [Tooltip("In the Editor use localhost. On the Quest use your PC's IP, e.g. ws://192.168.1.20:8765")]
        public string url = "ws://localhost:8765";
        public ReachyRig rig;

        public bool Connected => _connected;

        [Serializable]
        class Message
        {
            public string type;
            public Channels ch;
        }

        readonly ConcurrentQueue<string> _inbox = new ConcurrentQueue<string>();
        CancellationTokenSource _cts;
        volatile bool _connected;

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

        async Task RunAsync(CancellationToken ct)
        {
            bool warned = false;
            var buffer = new byte[16 * 1024];

            while (!ct.IsCancellationRequested)
            {
                using (var ws = new ClientWebSocket())
                {
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
                    }
                }

                try { await Task.Delay(2000, ct); }
                catch (OperationCanceledException) { break; }
            }
        }

        void Update()
        {
            // Only the newest pose matters, so skip any frames that piled up.
            string latest = null;
            while (_inbox.TryDequeue(out var m)) latest = m;
            if (latest == null || rig == null) return;

            var msg = JsonUtility.FromJson<Message>(latest);
            if (msg != null && msg.type == "pose") rig.Apply(msg.ch);
        }
    }
}
