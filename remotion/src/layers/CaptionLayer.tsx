import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import type {ThemeTokens} from '../design/tokens';

type CaptionWord = {text: string; start_ms: number; end_ms: number};

/**
 * CaptionLayer — mobile karaoke captions.
 *
 * Renders only words whose timing window contains the current frame so captions
 * never leak prior or future words into silent gaps.
 */
export const CaptionLayer: React.FC<{
  theme: ThemeTokens;
  words: CaptionWord[];
}> = ({theme, words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const frameMs = (frame / fps) * 1000;
  let activeWordSpans: React.ReactNode[] | null = null;

  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    if (frameMs >= word.start_ms && frameMs < word.end_ms) {
      activeWordSpans ??= [];
      activeWordSpans.push(
        <span
          key={`${word.start_ms}-${word.end_ms}-${i}`}
          style={{
            flex: '0 1 auto',
            fontSize: 44,
            fontWeight: 800,
            fontFamily: theme.font_body,
            color: theme.caption_highlight,
            textShadow: '0 3px 12px rgba(0,0,0,0.72)',
            lineHeight: 1.05,
            letterSpacing: '-0.02em',
          }}
        >
          {word.text}
        </span>,
      );
    }
  }

  if (activeWordSpans === null) {
    return null;
  }

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 220,
        paddingLeft: 60,
        paddingRight: 60,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          gap: '6px 14px',
          width: 'fit-content',
          maxWidth: 900,
          maxHeight: 118,
          overflow: 'hidden',
          padding: '18px 28px 20px',
          borderRadius: 30,
          background: 'rgba(6, 10, 24, 0.66)',
          boxShadow: '0 18px 44px rgba(0, 0, 0, 0.32)',
        }}
      >
        {activeWordSpans}
      </div>
    </AbsoluteFill>
  );
};
