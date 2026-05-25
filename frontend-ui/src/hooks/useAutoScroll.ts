import { RefObject, useEffect } from "react";

export function useAutoScroll<T extends HTMLElement>(ref: RefObject<T>, deps: unknown[] = []) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [ref, ...deps]);
}
