export type Track = {
  language: string;
  language_code: string;
  is_generated: boolean;
  is_translatable: boolean;
  translation_languages: { language: string; language_code: string }[];
};

export type Segment = {
  id: number;
  text: string;
  start: number;
  duration: number;
  end: number;
};

export type Transcript = {
  video_id: string;
  language: string;
  language_code: string;
  is_generated: boolean;
  segments: Segment[];
};

type ErrorPayload = { error?: { message?: string } };

async function request<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body)
  });
  const payload = (await response.json()) as T & ErrorPayload;
  if (!response.ok) {
    throw new Error(payload.error?.message ?? 'The request failed.');
  }
  return payload;
}

export const parseVideo = (input: string) => request<{ video_id: string; canonical_url: string }>('/api/video/parse', { input });
export const listTracks = (video_id: string) => request<{ video_id: string; tracks: Track[] }>('/api/transcripts/list', { video_id });
export const fetchTranscript = (body: {
  video_id: string;
  language_code: string;
  track_type: 'manual' | 'generated';
}) => request<Transcript>('/api/transcripts/fetch', { ...body, preserve_formatting: true });
