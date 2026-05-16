---
name: omk-youtube
description: "Extract and summarize YouTube video content via subtitle extraction. Trigger when user shares a YouTube URL (youtube.com or youtu.be), says 'summarize this video', 'watch this', '看看这个视频', or wants to understand video content without watching. Also trigger for video transcript extraction."
---

## Trigger Examples
- "帮我看看这个视频讲了什么 https://youtube.com/watch?v=xxx"
- "summarize this YouTube video"
- "提取这个视频的字幕"
- "这个 talk 讲了什么？ https://youtu.be/xxx"
- "translate this video's content to Chinese"

# Extração de legendas do YouTube

## Quando usar

O usuário compartilha uma URL do YouTube e quer entender o conteúdo (resumo, pontos-chave, tradução).

## Uso

```bash
# English subtitles (default)
bash skills/omk-youtube/scripts/yt-subtitle.sh "https://www.youtube.com/watch?v=XXXXX"

# Chinese subtitles
bash skills/omk-youtube/scripts/yt-subtitle.sh "https://www.youtube.com/watch?v=XXXXX" zh-Hans

# Save to file
bash skills/omk-youtube/scripts/yt-subtitle.sh "https://www.youtube.com/watch?v=XXXXX" en /tmp/subtitle.txt
```

## Workflow

1. Extraia legendas: `bash skills/omk-youtube/scripts/yt-subtitle.sh <url> [lang]`
2. Leia a saída (texto puro limpo, sem timestamps)
3. Resuma no idioma de preferência do usuário

## Dicas

- Para vídeos em inglês: extraia legendas `en`, resuma em chinês, melhor qualidade
- Para vídeos em chinês: extraia legendas `zh-Hans` diretamente
- Prioridade: legendas manuais > legendas auto-geradas > traduzidas automaticamente
- Requer: `yt-dlp` (`brew install yt-dlp`)
