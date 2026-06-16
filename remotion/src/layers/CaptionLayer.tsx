import React, {useMemo} from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {createTikTokStyleCaptions} from '@remotion/captions';
import type {Caption} from '@remotion/captions';
import type {ThemeTokens} from '../design/tokens';

type CaptionWord = {text: string; start_ms: number; end_ms: number};

/**
 * CaptionLayer — TikTok-style word-highlighted captions.
 *
 * Uses @remotion/captions createTikTokStyleCaptions for word grouping.
 * Current word gets caption_highlight color; past words get white.
 * Positioned in bottom 15% of frame, above danger zone.
 */
export const CaptionLayer: React.FC<{
  theme: ThemeTokens;
  words: CaptionWord[];
}> = ({theme, words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const frameMs = (frame / fps) * 1000;

  // Map to full Caption type expected by @remotion/captions
  const captions: Caption[] = useMemo(
    () =>
      words.map((w) => ({
        text: w.text,
        startMs: w.start_ms,
        endMs: w.end_ms,
        timestampMs: null,
        confidence: null,
      })),
    [words],
  );

  // Group words using TikTok-style caption grouper
  const result = useMemo(() => {
    if (captions.length === 0) return {pages: []};
    return createTikTokStyleCaptions({
      captions,
      combineTokensWithinMilliseconds: 800,
    });
  }, [captions]);

  // Find active page
  const activePage = result.pages.find(
    (p) => frameMs >= p.startMs && frameMs < p.startMs + p.durationMs,
  );
  if (!activePage || !activePage.tokens || activePage.tokens.length === 0) return null;

  const tokens = activePage.tokens;

  // Find current word within the page
  const currentIndex = tokens.findIndex(
    (t) => frameMs >= t.fromMs && frameMs < t.toMs,
  );

  // Current word index for highlighting
  const resolvedCurrent = currentIndex >= 0 ? currentIndex : tokens.length;

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 160,
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
          gap: '8px 12px',
          maxWidth: 960,
        }}
      >
        {tokens.map((token, i) => {
          const isCurrent = i === currentIndex;
          const isPast = i < resolvedCurrent;
          return (
            <span
              key={`${token.fromMs}-${i}`}
              style={{
                fontSize: 36,
                fontWeight: 700,
                fontFamily: theme.font_body,
                color: isCurrent
                  ? theme.caption_highlight
                  : isPast
                    ? '#ffffff'
                    : '#ffffff99',
                textShadow: '0 2px 8px rgba(0,0,0,0.5)',
                lineHeight: 1.3,
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
