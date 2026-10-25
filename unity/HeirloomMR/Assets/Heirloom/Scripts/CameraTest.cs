using System;
using System.IO;
using Meta.XR;
using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace Heirloom
{
    /// <summary>
    /// TEST: can the Quest 3's passthrough camera be read over Link in the Editor?
    /// Put this on any object (it adds PassthroughCameraAccess). Press Play, wait a few seconds,
    /// click the Game view and press C. It saves what the headset camera sees to E:\HEIRLOOM\camera_test\
    /// and logs what happened. Over Link this needs Meta Horizon Link v85+ and the headset on HzOS v85+.
    /// </summary>
    [RequireComponent(typeof(PassthroughCameraAccess))]
    public class CameraTest : MonoBehaviour
    {
        PassthroughCameraAccess _cam;
        float _nextStatus;

        void Awake() => _cam = GetComponent<PassthroughCameraAccess>();

        void Start()
        {
            Debug.Log($"[CameraTest] Supported on this headset: {PassthroughCameraAccess.IsSupported}. Press C in the Game view to take a test photo.");
        }

        void Update()
        {
            if (Time.time >= _nextStatus)
            {
                _nextStatus = Time.time + 5f;
                Debug.Log($"[CameraTest] playing: {_cam.IsPlaying}, resolution: {_cam.CurrentResolution}");
            }
            if (Pressed()) Snap();
        }

        void Snap()
        {
            if (!_cam.IsPlaying)
            {
                Debug.LogWarning("[CameraTest] The camera isn't playing. Check the Console for a PassthroughCameraAccess error (it names the Link / HzOS version it needs).");
                return;
            }
            var size = _cam.CurrentResolution;
            var colors = _cam.GetColors();
            if (!colors.IsCreated || colors.Length != size.x * size.y)
            {
                Debug.LogWarning("[CameraTest] Got no pixels back.");
                return;
            }
            var tex = new Texture2D(size.x, size.y, TextureFormat.RGBA32, false);
            tex.SetPixels32(colors.ToArray());
            tex.Apply();
            var folder = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "..", "camera_test"));
            Directory.CreateDirectory(folder);
            var path = Path.Combine(folder, $"test_{DateTime.Now:HHmmss}.jpg");
            File.WriteAllBytes(path, tex.EncodeToJPG(90));
            Destroy(tex);
            Debug.Log($"[CameraTest] Saved {size.x}x{size.y} photo to {path}");
        }

        static bool Pressed()
        {
#if ENABLE_INPUT_SYSTEM
            return Keyboard.current != null && Keyboard.current.cKey.wasPressedThisFrame;
#else
            return Input.GetKeyDown(KeyCode.C);
#endif
        }
    }
}
