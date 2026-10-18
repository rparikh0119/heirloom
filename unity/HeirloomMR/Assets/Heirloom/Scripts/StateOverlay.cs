using TMPro;
using UnityEngine;

namespace Heirloom
{
    /// <summary>Floating label above the robot showing what the brain is doing. First piece of "see its mind".</summary>
    [RequireComponent(typeof(TMP_Text))]
    public class StateOverlay : MonoBehaviour
    {
        public HeirloomLink link;
        public ReachyRig rig;
        public float heightAboveHead = 0.15f;

        TMP_Text _label;

        void Awake()
        {
            _label = GetComponent<TMP_Text>();
            _label.fontSize = 0.25f;
            _label.alignment = TextAlignmentOptions.Center;
            _label.rectTransform.sizeDelta = new Vector2(1f, 0.3f);
        }

        void LateUpdate()
        {
            if (link == null || rig == null) return;

            // Float above the head and always face the viewer.
            transform.position = rig.HeadRestWorld + Vector3.up * heightAboveHead;
            var cam = Camera.main;
            if (cam != null) transform.rotation = Quaternion.LookRotation(transform.position - cam.transform.position);

            if (!link.Connected) { _label.text = "<color=#888888>NO BRAIN</color>"; return; }

            string line;
            switch (link.BrainMode)
            {
                case "attend": line = link.UserDistance >= 0 ? $"NOTICED YOU  ·  {link.UserDistance:0.0} m" : "NOTICED YOU"; break;
                case "idle": line = "IDLE"; break;
                case "back_off": line = "GIVING YOU SPACE"; break;
                case "sleep": line = "ASLEEP"; break;
                case "sulk": line = "<color=#C0504D>OFFENDED</color>"; break;
                case "listening": line = "<color=#7FB3D5>LISTENING...</color>"; break;
                default: line = (link.BrainMode ?? "").ToUpperInvariant(); break;
            }
            if (!string.IsNullOrEmpty(link.BrainExpression))
                line += $"\n<size=70%><color=#B07CC6>{link.BrainExpression}</color></size>";
            _label.text = line;
        }
    }
}
