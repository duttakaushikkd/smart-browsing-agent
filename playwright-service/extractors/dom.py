from typing import Any
from playwright.async_api import Page


async def extract_compressed_dom(page: Page) -> dict[str, Any]:
    """Runs a script in the browser context to extract visible elements and tag them with references."""
    title = await page.title()
    url = page.url

    # JS script to find visible and interactive elements, and tag them with data-agent-ref
    script = """
    () => {
        // Clear previous agent refs
        document.querySelectorAll('[data-agent-ref]').forEach(el => el.removeAttribute('data-agent-ref'));

        const elements = [];
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_ELEMENT,
            {
                acceptNode: (node) => {
                    const rect = node.getBoundingClientRect();
                    const style = window.getComputedStyle(node);
                    if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
                        return NodeFilter.FILTER_ACCEPT;
                    }
                    return NodeFilter.FILTER_REJECT;
                }
            }
        );

        let node;
        let idCounter = 1;
        while (node = walker.nextNode()) {
            const tagName = node.tagName.toLowerCase();
            const role = node.getAttribute('role') || '';
            const text = (node.innerText || node.textContent || '').trim().substring(0, 100);
            
            // Check if interactive or interesting
            const isClickable = window.getComputedStyle(node).cursor === 'pointer' || 
                                ['a', 'button', 'input', 'select', 'textarea'].includes(tagName) ||
                                node.hasAttribute('onclick');
            
            if (isClickable || text.length > 5) {
                const refId = `el:${idCounter++}`;
                node.setAttribute('data-agent-ref', refId);

                let selector = `[data-agent-ref="${refId}"]`;
                
                elements.push({
                    type: tagName,
                    text: text,
                    selector: selector,
                    role: role,
                    target_ref: refId
                });
            }
            if (elements.length >= 100) break; // Limit elements size for planner context
        }
        return elements;
    }
    """
    try:
        visible_elements = await page.evaluate(script)
    except Exception:
        visible_elements = []

    return {
        "page_title": title,
        "current_url": url,
        "visible_elements": visible_elements,
    }
