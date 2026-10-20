using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Heirloom
{
    /// <summary>
    /// Animate Heirloom by hand and save the result as an expression the brain can play.
    /// Put this on the robot (next to ReachyRig). In Play mode, with the Game view focused:
    ///   K          capture a keyframe from the Preview Pose sliders
    ///   Backspace  remove the last keyframe
    ///   P          play back what you've captured
    ///   Enter      save to brain/expressions/[Expression Name].json
    ///   N          start over
    /// Then use the name as "motion" in any reaction file, and restart the brain.
    /// </summary>
    public class PoseRecorder : MonoBehaviour
    {
        public ReachyRig rig;

        [Tooltip("File name, no spaces. Becomes the 'motion' name in reaction files.")]
        public string expressionName = "my_expression";
        [TextArea] public string note = "What it does and why.";

        [Tooltip("Seconds between keyframes. Smaller = snappier.")]
        [Range(0.05f, 1f)] public float step = 0.25f;

        [Tooltip("Ticks the rig's Preview, so the sliders drive the robot instead of the brain.")]
        public bool recording;

        static readonly Channels Rest = new Channels();   // the resting pose; keyframes store offsets from it
        readonly List<(float t, Channels pose)> _keys = new List<(float, Channels)>();
        Coroutine _playing;
        bool _wasRecording;

        void Reset() { rig = GetComponent<ReachyRig>(); }

        void Update()
        {
            if (rig == null) return;
            if (recording != _wasRecording)      // only touch the rig's Preview when this changes
            {
                rig.preview = recording;
                _wasRecording = recording;
            }
            if (!recording) return;

            if (Pressed("k")) Capture();
            if (Pressed("backspace") && _keys.Count > 0)
            {
                _keys.RemoveAt(_keys.Count - 1);
                Debug.Log($"[Recorder] Removed last keyframe ({_keys.Count} left)");
            }
            if (Pressed("p")) Play();
            if (Pressed("enter")) Save();
            if (Pressed("n")) { _keys.Clear(); Debug.Log("[Recorder] Cleared"); }
        }

        void Capture()
        {
            float t = _keys.Count == 0 ? step : _keys[_keys.Count - 1].t + step;
            _keys.Add((t, Copy(rig.previewPose)));
            Debug.Log($"[Recorder] Keyframe {_keys.Count} at {t:0.00}s");
        }

        void Play()
        {
            if (_keys.Count == 0) return;
            if (_playing != null) StopCoroutine(_playing);
            _playing = StartCoroutine(PlayRoutine(Copy(rig.previewPose)));
        }

        IEnumerator PlayRoutine(Channels after)
        {
            // Same shape the brain plays: rest -> keyframes -> back to rest, smoothed between keys.
            var frames = new List<(float t, Channels pose)> { (0f, Copy(Rest)) };
            frames.AddRange(_keys);
            frames.Add((_keys[_keys.Count - 1].t + step * 1.5f, Copy(Rest)));
            float time = 0f, end = frames[frames.Count - 1].t;
            while (time < end)
            {
                for (int i = 0; i < frames.Count - 1; i++)
                {
                    if (time < frames[i].t || time >= frames[i + 1].t) continue;
                    float s = (time - frames[i].t) / (frames[i + 1].t - frames[i].t);
                    s = s * s * (3 - 2 * s);
                    Lerp(frames[i].pose, frames[i + 1].pose, s, rig.previewPose);
                }
                time += Time.deltaTime;
                yield return null;
            }
            Lerp(after, after, 0f, rig.previewPose);   // put the sliders back where they were
            _playing = null;
        }

        void Save()
        {
            if (_keys.Count == 0) { Debug.LogWarning("[Recorder] Nothing to save. Press K to capture keyframes."); return; }
            var folder = Path.GetFullPath(Path.Combine(Application.dataPath, "../../../brain/expressions"));
            if (!Directory.Exists(folder)) { Debug.LogError($"[Recorder] Can't find {folder}"); return; }

            var c = CultureInfo.InvariantCulture;
            var sb = new StringBuilder();
            sb.Append("{\n  \"note\": \"").Append(note.Replace("\"", "'").Replace("\n", " ")).Append("\",\n  \"keys\": [\n");
            sb.Append("    {\"t\": 0.0, \"ch\": {}},\n");
            foreach (var (t, pose) in _keys)
                sb.Append("    {\"t\": ").Append(t.ToString("0.###", c)).Append(", \"ch\": {").Append(Offsets(pose, c)).Append("}},\n");
            float endT = _keys[_keys.Count - 1].t + step * 1.5f;
            sb.Append("    {\"t\": ").Append(endT.ToString("0.###", c)).Append(", \"ch\": {}}\n  ]\n}\n");

            var path = Path.Combine(folder, expressionName.Trim().Replace(" ", "_") + ".json");
            File.WriteAllText(path, sb.ToString());
            Debug.Log($"[Recorder] Saved {_keys.Count} keyframes to {path}. Restart the brain to use it.");
        }

        /// <summary>Only the channels that differ from rest, written as JSON pairs.</summary>
        static string Offsets(Channels p, CultureInfo c)
        {
            var parts = new List<string>();
            void Add(string name, float value, float rest)
            {
                float d = value - rest;
                if (Mathf.Abs(d) > 0.01f) parts.Add($"\"{name}\": {d.ToString("0.###", c)}");
            }
            Add("head_pitch", p.head_pitch, Rest.head_pitch);
            Add("head_yaw", p.head_yaw, Rest.head_yaw);
            Add("head_roll", p.head_roll, Rest.head_roll);
            Add("base_yaw", p.base_yaw, Rest.base_yaw);
            Add("antenna_left", p.antenna_left, Rest.antenna_left);
            Add("antenna_right", p.antenna_right, Rest.antenna_right);
            Add("iris", p.iris, Rest.iris);
            Add("light", p.light, Rest.light);
            return string.Join(", ", parts);
        }

        static Channels Copy(Channels p) => new Channels
        {
            head_pitch = p.head_pitch, head_yaw = p.head_yaw, head_roll = p.head_roll, base_yaw = p.base_yaw,
            antenna_left = p.antenna_left, antenna_right = p.antenna_right, iris = p.iris, light = p.light
        };

        static void Lerp(Channels a, Channels b, float s, Channels into)
        {
            into.head_pitch = Mathf.Lerp(a.head_pitch, b.head_pitch, s);
            into.head_yaw = Mathf.Lerp(a.head_yaw, b.head_yaw, s);
            into.head_roll = Mathf.Lerp(a.head_roll, b.head_roll, s);
            into.base_yaw = Mathf.Lerp(a.base_yaw, b.base_yaw, s);
            into.antenna_left = Mathf.Lerp(a.antenna_left, b.antenna_left, s);
            into.antenna_right = Mathf.Lerp(a.antenna_right, b.antenna_right, s);
            into.iris = Mathf.Lerp(a.iris, b.iris, s);
            into.light = Mathf.Lerp(a.light, b.light, s);
        }

        static bool Pressed(string key)
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            if (kb == null) return false;
            switch (key)
            {
                case "k": return kb.kKey.wasPressedThisFrame;
                case "p": return kb.pKey.wasPressedThisFrame;
                case "n": return kb.nKey.wasPressedThisFrame;
                case "backspace": return kb.backspaceKey.wasPressedThisFrame;
                case "enter": return kb.enterKey.wasPressedThisFrame || kb.numpadEnterKey.wasPressedThisFrame;
                default: return false;
            }
#else
            switch (key)
            {
                case "k": return Input.GetKeyDown(KeyCode.K);
                case "p": return Input.GetKeyDown(KeyCode.P);
                case "n": return Input.GetKeyDown(KeyCode.N);
                case "backspace": return Input.GetKeyDown(KeyCode.Backspace);
                case "enter": return Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter);
                default: return false;
            }
#endif
        }
    }
}
