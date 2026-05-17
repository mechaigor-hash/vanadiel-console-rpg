export class AssetManager {
  constructor(manifest = {}) {
    this.manifest = manifest;
    this.images = new Map();
    this.sounds = new Map();
    this.audioContext = null;
  }

  async loadImage(key, src) {
    const img = new Image();
    img.src = src;
    await img.decode().catch(() => undefined);
    this.images.set(key, img);
    return img;
  }

  loadSound(key, spec) {
    if (typeof spec === "string") {
      const audio = new Audio(spec);
      audio.preload = "auto";
      this.sounds.set(key, { type: "file", audio });
      return audio;
    }
    this.sounds.set(key, { type: "synth", ...spec });
    return spec;
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
    if (sound.type === "file") {
      const clone = sound.audio.cloneNode();
      clone.volume = volume;
      clone.play().catch(() => undefined);
      return true;
    }
    return this.playTone(sound, volume);
  }

  playTone(sound, volume = 0.7) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return false;
    this.audioContext ??= new AudioContext();
    const ctx = this.audioContext;
    const now = ctx.currentTime;
    const duration = sound.duration ?? 0.12;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime((sound.volume ?? 0.18) * volume, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);
    gain.connect(ctx.destination);

    const tones = sound.tones ?? [sound.frequency ?? 440];
    tones.forEach((frequency, index) => {
      const osc = ctx.createOscillator();
      osc.type = sound.wave ?? "triangle";
      osc.frequency.setValueAtTime(frequency, now + index * 0.035);
      osc.connect(gain);
      osc.start(now + index * 0.035);
      osc.stop(now + duration + index * 0.035);
    });
    return true;
  }
}

export const defaultManifest = {
  images: {
    hero: "assets/images/hero-placeholder.svg",
    map: "assets/images/map-placeholder.svg",
    combat: "assets/images/combat-placeholder.svg",
    gathering: "assets/images/gathering-placeholder.svg",
  },
  sounds: {
    ui_confirm: { tones: [523, 659], duration: 0.12, wave: "triangle", volume: 0.14 },
    ui_cancel: { tones: [392, 330], duration: 0.14, wave: "sine", volume: 0.12 },
    combat_hit: { frequency: 130, duration: 0.1, wave: "sawtooth", volume: 0.1 },
    spell_cast: { tones: [440, 554, 659], duration: 0.18, wave: "triangle", volume: 0.12 },
    fish_tension: { tones: [247, 330], duration: 0.16, wave: "square", volume: 0.08 },
    fish_catch: { tones: [392, 523, 784], duration: 0.22, wave: "triangle", volume: 0.14 },
  },
};
