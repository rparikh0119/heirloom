using System;
using UnityEngine;

namespace Heirloom
{
    /// <summary>Turns WAV bytes (16-bit PCM, like the brain's chirps) into a Unity AudioClip.</summary>
    public static class WavUtility
    {
        public static AudioClip FromWav(byte[] wav, string clipName)
        {
            if (wav == null || wav.Length < 44 || wav[0] != 'R' || wav[1] != 'I' || wav[2] != 'F' || wav[3] != 'F')
            {
                Debug.LogWarning("[Heirloom] Not a WAV file");
                return null;
            }

            int channels = 1, sampleRate = 22050, bits = 16;
            int pos = 12;
            while (pos + 8 <= wav.Length)
            {
                string id = System.Text.Encoding.ASCII.GetString(wav, pos, 4);
                int size = BitConverter.ToInt32(wav, pos + 4);
                int body = pos + 8;
                if (id == "fmt ")
                {
                    channels = BitConverter.ToInt16(wav, body + 2);
                    sampleRate = BitConverter.ToInt32(wav, body + 4);
                    bits = BitConverter.ToInt16(wav, body + 14);
                }
                else if (id == "data")
                {
                    if (bits != 16) { Debug.LogWarning("[Heirloom] Only 16-bit WAV is supported"); return null; }
                    size = Math.Min(size, wav.Length - body);
                    int count = size / 2;
                    var samples = new float[count];
                    for (int i = 0; i < count; i++)
                        samples[i] = BitConverter.ToInt16(wav, body + i * 2) / 32768f;
                    var clip = AudioClip.Create(clipName, count / channels, channels, sampleRate, false);
                    clip.SetData(samples, 0);
                    return clip;
                }
                pos = body + size + (size % 2);   // chunks are padded to even sizes
            }
            Debug.LogWarning("[Heirloom] WAV had no data chunk");
            return null;
        }
    }
}
