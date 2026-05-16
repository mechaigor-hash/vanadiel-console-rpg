export class AssetManager {
  constructor(manifest = {}) {
    this.manifest = manifest;
    this.images = new Map();
    this.sounds = new Map();
  }

  async loadImage(key, src) {
    const img = new Image();
    img.src = src;
    await img.decode().catch(() => undefined);
    this.images.set(key, img);
    return img;
  }

  loadSound(key, src) {
    const audio = new Audio(src);
    audio.preload = "auto";
    this.sounds.set(key, audio);
    return audio;
  }

  async preload() {
    const imageEntries = Object.entries(this.manifest.images ?? {});
    const soundEntries = Object.entries(this.manifest.sounds ?? {});
    await Promise.all(imageEntries.map(([key, src]) => this.loadImage(key, src)));
    soundEntries.forEach(([key, src]) => this.loadSound(key, src));
  }

  play(key, volume = 0.7) {
    const sound = this.sounds.get(key);
    if (!sound) return false;
    const clone = sound.cloneNode();
    clone.volume = volume;
    clone.play().catch(() => undefined);
    return true;
  }
}

export const defaultManifest = {
  images: {
    // Example future keys: portrait_hume_male: "assets/images/portrait_hume_male.png"
  },
  sounds: {
    // Example future keys: ui_click: "assets/sounds/ui_click.ogg"
  },
};
