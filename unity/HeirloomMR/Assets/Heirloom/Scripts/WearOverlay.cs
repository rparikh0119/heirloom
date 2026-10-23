using System.Text;
using TMPro;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Heirloom
{
    /// <summary>
    /// Floating panel beside the robot showing how worn in it is (R64: make relationship stages visible).
    ///   DIALS   the five temperament dials. The bar spans everything wear can ever reach (0.5 +- limit),
    ///           the mark in the middle is out of the box, the fill is how far this home has moved it.
    ///   MOVES   the most used expressions. settled = weeks (hesitant to sure), character = years (the home's flavour).
    ///   RUST    after time apart. Warms back up with a few moments.
    /// Press W (Game view focused) to show or hide it.
    /// Two droids side by side: give the left one a negative Offset X so its panel sits on the outside.
    /// </summary>
    [RequireComponent(typeof(TMP_Text))]
    public class WearOverlay : MonoBehaviour
    {
        public HeirloomLink link;
        public ReachyRig rig;
        [Tooltip("Where the panel sits, relative to the robot's head: right, up, toward you (metres)")]
        public Vector3 offset = new Vector3(0.2f, 0.05f, 0f);
        public bool visible = true;
        [Tooltip("Text size in metres-ish. 0.2 is easy to read in the headset, 0.1 is compact")]
        public float textSize = 0.2f;
        [Tooltip("How many expressions to list, most used first")]
        public int movesShown = 4;

        const string Cream = "#E9DFC8", Oxblood = "#B5413A", Dim = "#6E675C", Rust = "#C77B3A";
        static readonly string[] DialNames = { "curiosity", "sass", "boldness", "energy", "warmth" };

        TMP_Text _label;
        readonly StringBuilder _sb = new StringBuilder();

        void Awake()
        {
            _label = GetComponent<TMP_Text>();
            _label.alignment = TextAlignmentOptions.TopLeft;
            _label.richText = true;
            Resize();
        }

        void Resize()
        {
            _label.fontSize = textSize;
            _label.rectTransform.sizeDelta = new Vector2(9f * textSize, 6.5f * textSize);
            // Anchored by the edge nearest the robot, so the panel always starts beside the head.
            _label.rectTransform.pivot = new Vector2(offset.x >= 0 ? 0f : 1f, 0.5f);
        }

        void Update()
        {
            if (TogglePressed()) visible = !visible;
            if (!Mathf.Approximately(_label.fontSize, textSize)) Resize();   // so you can change it while playing
        }

        void LateUpdate()
        {
            if (link == null || rig == null) return;
            _label.enabled = visible;
            if (!visible) return;

            var cam = Camera.main;
            var right = cam != null ? cam.transform.right : rig.transform.right;
            transform.position = rig.HeadRestWorld + right * offset.x + Vector3.up * offset.y
                                 + (cam != null ? (cam.transform.position - rig.HeadRestWorld).normalized * offset.z : Vector3.zero);
            if (cam != null) transform.rotation = Quaternion.LookRotation(transform.position - cam.transform.position);

            _label.text = Build(link.Connected ? link.BrainWear : null);
        }

        string Build(HeirloomLink.Wear w)
        {
            _sb.Clear();
            _sb.Append("<mspace=0.55em>");
            if (w == null) { _sb.Append($"<color={Dim}>WEAR · no brain</color>"); return _sb.ToString(); }
            if (!w.learning)
            {
                _sb.Append($"<size=150%><color={Cream}><b>{(string.IsNullOrEmpty(w.label) ? "WEAR" : w.label)}</b></color></size>\n<color={Dim}>no cartridge, not learning</color>");
                return _sb.ToString();
            }

            string name = string.IsNullOrEmpty(w.label) ? "WEAR" : w.label;
            _sb.Append($"<size=150%><color={Cream}><b>{name}</b></color></size>\n\n");
            var d = w.dials;
            float[] values = { d.curiosity, d.sass, d.boldness, d.energy, d.warmth_speed };
            for (int i = 0; i < values.Length; i++)
                _sb.Append($"<color={Cream}>{DialNames[i],-10}</color>{DialBar(values[i], w.limit)} <color={Dim}>{values[i]:0.00}</color>\n");

            _sb.Append($"\n<color={Dim}>{"",-10}settled    character</color>\n");
            int n = w.moves == null ? 0 : Mathf.Min(movesShown, w.moves.Length);
            if (n == 0) _sb.Append($"<color={Dim}>every move brand new</color>\n");
            for (int i = 0; i < n; i++)
            {
                var m = w.moves[i];
                _sb.Append($"<color={Cream}>{Trim(m.name, 9),-10}</color>{Bar(m.settled, 10, Oxblood)} {Bar(m.character, 10, Cream)} <color={Dim}>{m.uses}</color>\n");
            }

            _sb.Append("\n");
            if (w.rust > 0.01f) _sb.Append($"<color={Rust}>RUSTY {w.rust:0.00}</color>  <color={Dim}>warming up</color>\n");
            else _sb.Append($"<color={Dim}>in practice</color>\n");
            _sb.Append($"<color={Dim}>notices you at {w.notice_m:0.0} m</color>");
            return _sb.ToString();
        }

        /// <summary>21 cells across 0.5 +- limit. Middle mark = out of the box, fill = how far this home moved it.</summary>
        static string DialBar(float value, float limit, int cells = 21)
        {
            int mid = cells / 2;
            float t = limit > 0 ? Mathf.Clamp((value - 0.5f) / limit, -1f, 1f) : 0f;
            int pos = mid + Mathf.RoundToInt(t * mid);
            var sb = new StringBuilder();
            for (int i = 0; i < cells; i++)
            {
                bool filled = (i > mid && i <= pos) || (i < mid && i >= pos);
                if (i == mid) sb.Append($"<color={Cream}>|</color>");
                else if (filled) sb.Append($"<color={Oxblood}>|</color>");
                else sb.Append($"<color={Dim}>·</color>");
            }
            return sb.ToString();
        }

        static string Bar(float v, int cells, string color)
        {
            int full = Mathf.RoundToInt(Mathf.Clamp01(v) * cells);
            return $"<color={color}>{new string('|', full)}</color><color={Dim}>{new string('·', cells - full)}</color>";
        }

        static string Trim(string s, int max) => string.IsNullOrEmpty(s) ? "" : (s.Length <= max ? s : s.Substring(0, max));

        static bool TogglePressed()
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            return kb != null && kb.wKey.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.W);
#endif
        }
    }
}
