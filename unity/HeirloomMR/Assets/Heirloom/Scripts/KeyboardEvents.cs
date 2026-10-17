using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Heirloom
{
    /// <summary>
    /// Editor stand-ins for gestures and voice, until the headset session.
    /// Click the Game view first so it receives key presses.
    /// 1 wave · 2 good job · 3 not now · 4 go to sleep · 5 wake up · 6 curious
    /// </summary>
    public class KeyboardEvents : MonoBehaviour
    {
        public HeirloomLink link;

        static readonly string[] Events = { "wave", "good", "not_now", "sleep", "wake", "curious" };

        void Update()
        {
            if (link == null) return;
            for (int i = 0; i < Events.Length; i++)
            {
                if (Pressed(i + 1))
                {
                    link.SendEvent(Events[i]);
                    Debug.Log($"[Heirloom] Sent event: {Events[i]}");
                }
            }
        }

        static bool Pressed(int number)
        {
#if ENABLE_INPUT_SYSTEM
            var kb = Keyboard.current;
            if (kb == null) return false;
            switch (number)
            {
                case 1: return kb.digit1Key.wasPressedThisFrame;
                case 2: return kb.digit2Key.wasPressedThisFrame;
                case 3: return kb.digit3Key.wasPressedThisFrame;
                case 4: return kb.digit4Key.wasPressedThisFrame;
                case 5: return kb.digit5Key.wasPressedThisFrame;
                case 6: return kb.digit6Key.wasPressedThisFrame;
                default: return false;
            }
#else
            return Input.GetKeyDown(KeyCode.Alpha0 + number);
#endif
        }
    }
}
