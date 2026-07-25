import {Config} from '@remotion/cli/config';

// The render environment provides its own Chromium (Playwright's build);
// pointing Remotion at it avoids a browser download at render time.
if (process.env.REMOTION_BROWSER) {
  Config.setBrowserExecutable(process.env.REMOTION_BROWSER);
}
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
