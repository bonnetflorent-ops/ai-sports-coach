'use client';

import { useMemo } from 'react';
import { marked } from 'marked';

// Configure marked pour le rendu du chat
marked.setOptions({
  breaks: true,      // sauts de ligne → <br>
  gfm: true,         // GitHub Flavored Markdown (tables, strikethrough, etc.)
});

interface MarkdownTextProps {
  content: string;
}

/**
 * Convertit le markdown en HTML et l'affiche avec les styles du chat.
 * Utilisé par MessageBubble (message complet) et StreamingText (streaming).
 *
 * Sécurité : le contenu vient du backend (LLM) — pas d'HTML utilisateur.
 * On désactive quand même le HTML brut pour éviter les injections accidentelles.
 */
export function MarkdownText({ content }: MarkdownTextProps) {
  const html = useMemo(() => {
    const parsed = marked.parse(content, { async: false });
    return typeof parsed === 'string' ? parsed : content;
  }, [content]);

  return (
    <div
      className="text-sm markdown-content"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
