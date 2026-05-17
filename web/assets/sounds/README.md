# Sound placeholders

The web engine currently uses tiny Web Audio synth tones declared in `web/src/engine/assets.js` so the prototype has UI, combat, spell, and fishing feedback without binary assets.

Future `.ogg`/`.mp3` files can replace any manifest sound key by changing the value from a synth object to a file path, for example:

```js
ui_confirm: "assets/sounds/ui_confirm.ogg"
```
