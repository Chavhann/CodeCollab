import React from "react";

const ICONS = {
  python:     { symbol: "🐍",     label: "Python" },
  javascript: { symbol: "⚡",      label: "JavaScript" },
  typescript: { symbol: "🔷",     label: "TypeScript" },
  java:       { symbol: "☕",      label: "Java" },
  c:          { symbol: "⟨C⟩",    label: "C" },
  cpp:        { symbol: "⟨C++⟩",  label: "C++" },
  rust:       { symbol: "🦀",      label: "Rust" },
  go:         { symbol: "🐹",      label: "Go" },
  ruby:       { symbol: "💎",      label: "Ruby" },
  php:        { symbol: "🐘",      label: "PHP" },
  csharp:     { symbol: "🎯",      label: "C#" },
  kotlin:     { symbol: "🦇",      label: "Kotlin" },
  swift:      { symbol: "🍎",      label: "Swift" },
  dart:       { symbol: "◆",       label: "Dart" },
  r:          { symbol: "🧪",      label: "R" },
  matlab:     { symbol: "∿M",      label: "MATLAB" },
  perl:       { symbol: "🐪",      label: "Perl" },
  shell:      { symbol: "🐚",      label: "Shell / Bash" },
  html:       { symbol: "🌐",      label: "HTML" },
  css:        { symbol: "🎨",      label: "CSS" },
  scss:       { symbol: "🧩",      label: "SCSS" },
  json:       { symbol: "🧬",      label: "JSON" },
  markdown:   { symbol: "📝",      label: "Markdown" },
  jupyter:    { symbol: "📓",      label: "Jupyter Notebook" },
  sql:        { symbol: "🗃️",     label: "SQL" },
  xml:        { symbol: "</>",     label: "XML" },
  yaml:       { symbol: "YAML",    label: "YAML" },
  toml:       { symbol: "⚙",      label: "TOML" },
  docker:     { symbol: "📦",      label: "Dockerfile" },
  plaintext:  { symbol: "◇",      label: "Plain Text" },
};

function LanguageIcon({ language, className = "" }) {
  const icon = ICONS[language] || ICONS.plaintext;

  return (
    <span
      className={`language-icon language-icon-${language || "plaintext"} ${className}`.trim()}
      title={icon.label}
      aria-label={icon.label}
      role="img"
    >
      {icon.symbol}
    </span>
  );
}

export { ICONS };
export default LanguageIcon;





