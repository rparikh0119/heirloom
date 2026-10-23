using System.Collections.Generic;
using UnityEngine;

namespace Heirloom
{
    /// <summary>
    /// TESTING AID, not the real wear look. Tints the robot's shell warmer and less shiny the more
    /// worn in it is, so a fresh and a worn droid side by side read as different at a glance.
    /// The real wear (enamel worn to bare metal where hands touch) is a design job for the custom droid.
    /// Put this on the robot (the object with ReachyRig) and assign its link.
    /// </summary>
    public class WearTint : MonoBehaviour
    {
        public HeirloomLink link;
        [Range(0f, 1f)] public float strength = 1f;
        [Tooltip("What a fully worn shell is multiplied by: warm, like aged ivory")]
        public Color wornTint = new Color(1f, 0.8f, 0.58f);
        [Tooltip("How much of its shine a fully worn shell keeps")]
        [Range(0f, 1f)] public float wornShine = 0.3f;

        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");   // URP Lit
        static readonly int Smoothness = Shader.PropertyToID("_Smoothness");

        readonly List<Material> _mats = new List<Material>();
        readonly List<Color> _color = new List<Color>();
        readonly List<float> _shine = new List<float>();
        float _shown;

        /// <summary>0 = brand new, 1 = worn for years. Most of it comes from the slow character layer.</summary>
        public float Worn { get; private set; }

        void Start()
        {
            foreach (var r in GetComponentsInChildren<Renderer>(true))
            {
                foreach (var m in r.materials)          // instances, so the shared asset is never changed
                {
                    if (m == null || !m.HasProperty(BaseColor)) continue;
                    _mats.Add(m);
                    _color.Add(m.GetColor(BaseColor));
                    _shine.Add(m.HasProperty(Smoothness) ? m.GetFloat(Smoothness) : -1f);
                }
            }
        }

        void Update()
        {
            Worn = Amount(link != null && link.Connected ? link.BrainWear : null);
            _shown = Mathf.MoveTowards(_shown, Worn * strength, Time.deltaTime * 0.5f);   // eases when you switch droids
            for (int i = 0; i < _mats.Count; i++)
            {
                _mats[i].SetColor(BaseColor, Color.Lerp(_color[i], _color[i] * wornTint, _shown));
                if (_shine[i] >= 0f) _mats[i].SetFloat(Smoothness, Mathf.Lerp(_shine[i], _shine[i] * wornShine, _shown));
            }
        }

        static float Amount(HeirloomLink.Wear w)
        {
            if (w == null || !w.learning || w.moves == null || w.moves.Length == 0) return 0f;
            int n = Mathf.Min(3, w.moves.Length);      // the moves it does most (the list comes most used first)
            float settled = 0f, character = 0f;
            for (int i = 0; i < n; i++) { settled += w.moves[i].settled; character += w.moves[i].character; }
            return Mathf.Clamp01(0.3f * settled / n + 0.7f * character / n);
        }
    }
}
