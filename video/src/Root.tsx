import React from 'react';
import {Composition} from 'remotion';
import {Demo, TOTAL_FRAMES, FPS} from './Demo';

export const Root: React.FC = () => (
  <Composition
    id="gemma-demo"
    component={Demo}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={1920}
    height={1080}
  />
);
