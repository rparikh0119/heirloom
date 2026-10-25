using System;
using Meta.XR;
using UnityEngine;

namespace Heirloom
{
    /// <summary>
    /// The droid's camera in MR. When the brain says "capture" (after the countdown), grabs a frame
    /// from the Quest 3's passthrough camera and sends it to the brain as a JPEG, which keeps it in the
    /// cartridge journal. Never automatic: the brain only asks when you said "take a picture" (D02).
    /// In MR it photographs what you're looking at. The custom droid will use its own camera.
    /// Put this on any object and assign the link. Turn off CameraTest (only one can use the camera).
    /// Over Link it needs "Passthrough Camera API permissions" on in the Meta Horizon Link app.
    /// </summary>
    [RequireComponent(typeof(PassthroughCameraAccess))]
    public class PhotoCapture : MonoBehaviour
    {
        public HeirloomLink link;
        [Range(50, 100)] public int jpegQuality = 85;

        [Serializable] class PhotoMessage { public string type = "photo"; public string image_b64; }

        PassthroughCameraAccess _cam;

        void Awake() => _cam = GetComponent<PassthroughCameraAccess>();
        void OnEnable() { if (link != null) link.CaptureRequested += Capture; }
        void OnDisable() { if (link != null) link.CaptureRequested -= Capture; }

        void Capture()
        {
            if (_cam == null || !_cam.IsPlaying)
            {
                Debug.LogWarning("[Heirloom] Asked for a photo, but the camera isn't running. Is 'Passthrough Camera API permissions' on in the Link app?");
                return;
            }
            var size = _cam.CurrentResolution;
            var colors = _cam.GetColors();
            if (!colors.IsCreated || colors.Length != size.x * size.y)
            {
                Debug.LogWarning("[Heirloom] The camera gave no pixels.");
                return;
            }
            var tex = new Texture2D(size.x, size.y, TextureFormat.RGBA32, false);
            tex.SetPixels32(colors.ToArray());
            tex.Apply();
            var jpg = tex.EncodeToJPG(jpegQuality);
            Destroy(tex);
            link.Send(JsonUtility.ToJson(new PhotoMessage { image_b64 = Convert.ToBase64String(jpg) }));
            Debug.Log($"[Heirloom] Took a {size.x}x{size.y} photo ({jpg.Length / 1024} KB), sent to the brain");
        }
    }
}
