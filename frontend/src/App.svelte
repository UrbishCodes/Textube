<script lang="ts">
  import { fetchTranscript, listTracks, parseVideo, type Segment, type Track, type Transcript } from './lib/api';

  type Format = 'plain' | 'timestamped' | 'speaker' | 'srt' | 'vtt' | 'json' | 'csv' | 'markdown';
  let input = '';
  let videoId = '';
  let canonicalUrl = '';
  let tracks: Track[] = [];
  let selectedTrack = '';
  let transcript: Transcript | null = null;
  let format: Format = 'plain';
  let loading = false;
  let progress = '';
  let error = '';
  let notice = '';
  let speakerLabels: Record<number, string> = {};

  $: selected = tracks.find((track) => `${track.language_code}:${track.is_generated ? 'generated' : 'manual'}` === selectedTrack);
  $: output = transcript ? formatTranscript(transcript, format, speakerLabels) : '';
  $: duration = transcript && transcript.segments.length
    ? transcript.segments[transcript.segments.length - 1].end
    : 0;

  async function submit() {
    if (!input.trim() || loading) return;
    loading = true;
    error = '';
    notice = '';
    try {
      progress = 'Checking video';
      const parsed = await parseVideo(input);
      progress = 'Finding transcripts';
      const discovered = await listTracks(parsed.video_id);
      if (!discovered.tracks.length) throw new Error('This video does not have accessible transcripts.');
      videoId = parsed.video_id;
      canonicalUrl = parsed.canonical_url;
      tracks = discovered.tracks;
      const preferred = discovered.tracks.find((track) => !track.is_generated && track.language_code === 'en')
        ?? discovered.tracks.find((track) => track.is_generated && track.language_code === 'en')
        ?? discovered.tracks.find((track) => !track.is_generated)
        ?? discovered.tracks[0];
      selectedTrack = `${preferred.language_code}:${preferred.is_generated ? 'generated' : 'manual'}`;
      await loadTrack(preferred);
    } catch (caught) {
      error = caught instanceof Error ? caught.message : 'Unable to retrieve this transcript.';
    } finally {
      loading = false;
      progress = '';
    }
  }

  async function loadTrack(track = selected) {
    if (!track || !videoId) return;
    loading = true;
    error = '';
    notice = '';
    try {
      progress = 'Fetching transcript';
      transcript = await fetchTranscript({
        video_id: videoId,
        language_code: track.language_code,
        track_type: track.is_generated ? 'generated' : 'manual'
      });
      speakerLabels = {};
    } catch (caught) {
      error = caught instanceof Error ? caught.message : 'Unable to fetch this transcript.';
    } finally {
      loading = false;
      progress = '';
    }
  }

  function onTrackChange() {
    const track = tracks.find((item) => `${item.language_code}:${item.is_generated ? 'generated' : 'manual'}` === selectedTrack);
    if (track) void loadTrack(track);
  }

  async function copyOutput() {
    try {
      await navigator.clipboard.writeText(output);
      notice = 'Copied to clipboard.';
    } catch {
      notice = 'Copy failed. Select the preview text and copy it manually.';
    }
  }

  function downloadOutput() {
    if (!transcript) return;
    const extension = format === 'plain' || format === 'timestamped' || format === 'speaker' ? 'txt' : format;
    const blob = new Blob([output], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `youtube_${transcript.video_id}_${transcript.language_code}.${extension}`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function assignSpeaker(segment: Segment, value: string) {
    speakerLabels = { ...speakerLabels, [segment.id]: value };
  }

  function formatTimestamp(seconds: number, milliseconds = false) {
    const total = Math.max(0, Math.round(seconds * 1000));
    const hours = Math.floor(total / 3600000);
    const minutes = Math.floor((total % 3600000) / 60000);
    const secs = Math.floor((total % 60000) / 1000);
    const ms = total % 1000;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}${milliseconds ? `.${ms.toString().padStart(3, '0')}` : ''}`;
  }

  function formatTranscript(value: Transcript, selectedFormat: Format, labels: Record<number, string>) {
    if (selectedFormat === 'json') return JSON.stringify(value.segments.map(({ id, end, ...segment }) => segment), null, 2);
    if (selectedFormat === 'csv') {
      const rows = [['index', 'start', 'duration', 'end', 'speaker', 'text'], ...value.segments.map((segment, index) => [
        String(index + 1), String(segment.start), String(segment.duration), String(segment.end), labels[segment.id] ?? '', segment.text
      ])];
      return rows.map((row) => row.map((cell) => `"${cell.replaceAll('"', '""')}"`).join(',')).join('\n');
    }
    if (selectedFormat === 'markdown') {
      return `# Transcript\n\nSource: ${canonicalUrl}\nLanguage: ${value.language}\n\n${value.segments.map((segment) => `- **${formatTimestamp(segment.start)}** — ${segment.text}`).join('\n')}\n`;
    }
    if (selectedFormat === 'srt' || selectedFormat === 'vtt') {
      const cues = value.segments.map((segment, index) => {
        const start = formatTimestamp(segment.start, true);
        const end = formatTimestamp(segment.end > segment.start ? segment.end : segment.start + 0.1, true);
        const text = labels[segment.id] && selectedFormat === 'srt' ? `${labels[segment.id]}: ${segment.text}` : segment.text;
        return `${selectedFormat === 'srt' ? `${index + 1}\n` : ''}${start.replace('.', selectedFormat === 'srt' ? ',' : '.')} --> ${end.replace('.', selectedFormat === 'srt' ? ',' : '.')}\n${text}`;
      }).join('\n\n');
      return selectedFormat === 'vtt' ? `WEBVTT\n\n${cues}\n` : `${cues}\n`;
    }
    return value.segments.map((segment) => {
      const prefix = selectedFormat !== 'plain' ? `[${formatTimestamp(segment.start)}] ` : '';
      const speaker = selectedFormat === 'speaker' && labels[segment.id] ? `${labels[segment.id]}: ` : '';
      return `${prefix}${speaker}${segment.text}`;
    }).join('\n');
  }
</script>

<svelte:head><title>Transcript</title></svelte:head>

<main>
  <header>
    <div class="brand"><span class="mark">T</span><span>Transcript</span></div>
    <span class="status"><i></i> Local / Ready</span>
  </header>

  <section class="hero">
    <p class="eyebrow">YOUTUBE TRANSCRIPT TOOL</p>
    <h1>Turn a video into a transcript.</h1>
    <p class="intro">Fetch captions locally, refine the output, and export it in the format you need.</p>
    <form on:submit|preventDefault={submit}>
      <input bind:value={input} aria-label="YouTube URL or video ID" placeholder="Paste a YouTube link or video ID" maxlength="2048" />
      <button disabled={loading}>{loading ? 'Working…' : 'Get transcript'} <span>↗</span></button>
    </form>
    {#if error}<p class="message error">{error}</p>{/if}
    {#if progress}<p class="progress"><span class="spinner"></span>{progress}…</p>{/if}
  </section>

  {#if transcript}
    <section class="workspace">
      <div class="meta">
        <div><span class="label">VIDEO</span><a href={canonicalUrl} target="_blank" rel="noreferrer">{videoId} ↗</a></div>
        <div><span class="label">LANGUAGE</span><strong>{transcript.language}</strong> <span class="badge">{transcript.is_generated ? 'AUTO-GENERATED' : 'MANUAL'}</span></div>
        <select bind:value={selectedTrack} on:change={onTrackChange} aria-label="Transcript language">
          {#each tracks as track}<option value={`${track.language_code}:${track.is_generated ? 'generated' : 'manual'}`}>{track.language} · {track.is_generated ? 'Auto-generated' : 'Manual'}</option>{/each}
        </select>
      </div>
      <div class="toolbar">
        <label>FORMAT <select bind:value={format}><option value="plain">Plain text</option><option value="timestamped">Timestamped text</option><option value="speaker">Speaker-labeled text</option><option value="srt">SRT subtitles</option><option value="vtt">WebVTT subtitles</option><option value="json">JSON</option><option value="csv">CSV</option><option value="markdown">Markdown</option></select></label>
        <div class="actions"><button class="secondary" on:click={copyOutput}>Copy</button><button on:click={downloadOutput}>Download ↓</button></div>
      </div>
      {#if notice}<p class="message success">{notice}</p>{/if}
      {#if format === 'speaker'}<p class="hint">Speaker labels are manual annotations. Assign them below; none are inferred.</p>{/if}
      <div class="preview-wrap"><pre class="preview">{output}</pre></div>
      {#if format === 'speaker'}
        <details><summary>Assign speakers</summary>
          <div class="annotations">{#each transcript.segments as segment}<label><span>{formatTimestamp(segment.start)}</span><input value={speakerLabels[segment.id] ?? ''} placeholder="Optional speaker name" on:input={(event) => assignSpeaker(segment, event.currentTarget.value)} /></label>{/each}</div>
        </details>
      {/if}
      <p class="stats">{transcript.segments.length} segments · approximately {Math.round(duration)} seconds</p>
    </section>
  {:else}
    <section class="empty"><div class="empty-icon">↳</div><h2>Your transcript will appear here</h2><p>Paste a YouTube URL above to get started. Nothing leaves your computer except the request to YouTube.</p></section>
  {/if}
</main>
