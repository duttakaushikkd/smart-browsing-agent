import { useEffect, useMemo, useState } from "react";

type UseTypewriterOptions = {
  text: string;
  speed?: number;
  enabled?: boolean;
};

export function useTypewriter({ text, speed = 14, enabled = true }: UseTypewriterOptions) {
  const safeText = useMemo(() => text ?? "", [text]);
  const [displayText, setDisplayText] = useState(safeText);

  useEffect(() => {
    if (!enabled) {
      setDisplayText(safeText);
      return;
    }

    setDisplayText("");
    let index = 0;

    const timer = window.setInterval(() => {
      index += 1;
      setDisplayText(safeText.slice(0, index));

      if (index >= safeText.length) {
        window.clearInterval(timer);
      }
    }, speed);

    return () => window.clearInterval(timer);
  }, [enabled, safeText, speed]);

  return displayText;
}
