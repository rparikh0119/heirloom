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
    ///   NOW     the moment happening now (the 10 am hello), the chirp it answered with, whose habit it is.
    ///   LEARNING (run.py --learn) the move it just chose for a situation, how often it worked, landed or missed.
    ///   HABITS  every moment it has noticed. Turn off Show Moments for the older, shorter panel.
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
        [Tooltip("Show the clock, the moment happening now, and the habits it knows (moments + dialect)")]
        public bool showMoments = true;
        [Tooltip("How many habits to list")]
        public int habitsShown = 4;

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
            _label.rectTransform.sizeDelta = new Vector2(9f * textSize, (showMoments ? 10f : 6.5f) * textSize);
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
            _sb.Append($"<size=150%><color={Cream}><b>{name}</b></color></size>\n");
            if (showMoments && !string.IsNullOrEmpty(w.clock))
                _sb.Append($"<color={Dim}>{w.clock}{(w.clock_demo ? "  demo clock" : "")}</color>\n");
            _sb.Append("\n");
            if (showMoments && !string.IsNullOrEmpty(w.moment)) AppendMoment(w);
            if (w.learn_on) AppendLearning(w);
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
            if (showMoments) AppendHabits(w);
            return _sb.ToString();
        }

        /// <summary>The moment happening now, big, so it reads on camera: what it is, the chirp it used, whose it is.</summary>
        void AppendMoment(HeirloomLink.Wear w)
        {
            _sb.Append($"<size=120%><color={Oxblood}><b>NOW  {Trim(w.moment, 28)}</b></color></size>\n");
            if (!string.IsNullOrEmpty(w.moment_chirp)) _sb.Append($"<color={Cream}>{w.moment_chirp}</color>\n");
            if (w.moment_lines != null)
                foreach (var line in w.moment_lines) _sb.Append($"<color={Dim}>{Trim(line, 36)}</color>\n");
            _sb.Append("\n");
        }

        /// <summary>Learning loop v0: what it just chose, how often that worked, and whether it landed.</summary>
        void AppendLearning(HeirloomLink.Wear w)
        {
            _sb.Append($"<color={Dim}>LEARNING</color>\n");
            if (string.IsNullOrEmpty(w.learn_line)) { _sb.Append($"<color={Dim}>nothing tried yet</color>\n\n"); return; }
            _sb.Append($"<color={Cream}>{Trim(w.learn_line, 40)}</color>\n");
            if (w.learn_explore) _sb.Append($"<color={Rust}>trying something new</color>\n");
            if (!string.IsNullOrEmpty(w.learn_reward))
                _sb.Append($"<color={(w.learn_reward.StartsWith("landed") ? Oxblood : Dim)}>{w.learn_reward}</color>\n");
            _sb.Append("\n");
        }

        /// <summary>Every habit it has noticed. The one happening now is lit.</summary>
        void AppendHabits(HeirloomLink.Wear w)
        {
            int n = w.habits == null ? 0 : Mathf.Min(habitsShown, w.habits.Length);
            _sb.Append($"\n\n<color={Dim}>HABITS</color>\n");
            if (n == 0) { _sb.Append($"<color={Dim}>none noticed yet</color>"); return; }
            for (int i = 0; i < n; i++)
            {
                bool now = i == w.habit_now;
                _sb.Append($"<color={(now ? Oxblood : Cream)}>{(now ? "> " : "  ")}{Trim(w.habits[i], 34)}</color>\n");
            }
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
