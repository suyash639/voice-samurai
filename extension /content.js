// Voice Samurai Content Script
// Runs in page context to scrape DOM and execute actions

// Global state
const isRecording = false
const mediaRecorder = null
const audioChunks = []

// Declare chrome variable
const chrome = window.chrome

// Get simplified DOM for LLM processing
function getSimplifiedDOM() {
    const elements = []
    const elementMap = new Map()
    let id = 0

    // Target interactive elements
    const selectors = ["a", "button", "input", "select", "textarea", '[role="button"]', '[role="link"]', "[onclick]"]
    const nodeList = document.querySelectorAll(selectors.join(","))

    nodeList.forEach((el) => {
        try {
            // Check if element is visible
            const rect = el.getBoundingClientRect()
            if (rect.width <= 0 || rect.height <= 0) return

            const vId = `v-${id}`
            id++

            // Assign unique identifier
            el.setAttribute("data-v-id", vId)
            elementMap.set(vId, el)

            // Extract element info
            const text = el.textContent?.trim().substring(0, 100) || ""
            const placeholder = el.placeholder || ""
            const type = el.type || ""
            const tag = el.tagName.toLowerCase()

            // Get aria labels if available
            const ariaLabel = el.getAttribute("aria-label") || ""

            const elementInfo = {
                id: vId,
                tag: tag,
                text: text,
                placeholder: placeholder,
                type: type,
                ariaLabel: ariaLabel,
                x: Math.round(rect.left),
                y: Math.round(rect.top),
                width: Math.round(rect.width),
                height: Math.round(rect.height),
            }

            elements.push(elementInfo)
        } catch (e) {
            console.error("[v0] Error processing element:", e)
        }
    })

    return elements
}

// Execute action plan from backend
async function executeActions(actions) {
    if (!actions || !Array.isArray(actions)) return

    for (const action of actions) {
        try {
            const { type, target, value, duration } = action

            switch (type) {
                case "click":
                    if (target) {
                        const element = document.querySelector(`[data-v-id="${target}"]`)
                        if (element) {
                            element.scrollIntoView({ behavior: "smooth", block: "center" })
                            await new Promise((resolve) => setTimeout(resolve, 300))
                            element.click()
                            console.log("[v0] Clicked element:", target)
                        }
                    }
                    break

                case "fill":
                    if (target && value) {
                        const element = document.querySelector(`[data-v-id="${target}"]`)
                        if (element && (element.tagName === "INPUT" || element.tagName === "TEXTAREA")) {
                            element.scrollIntoView({ behavior: "smooth", block: "center" })
                            await new Promise((resolve) => setTimeout(resolve, 300))
                            element.focus()
                            element.value = value
                            element.dispatchEvent(new Event("input", { bubbles: true }))
                            element.dispatchEvent(new Event("change", { bubbles: true }))
                            console.log("[v0] Filled element:", target, "with value:", value)
                        }
                    }
                    break

                case "scroll":
                    window.scrollBy({
                        left: value?.x || 0,
                        top: value?.y || 0,
                        behavior: "smooth",
                    })
                    console.log("[v0] Scrolled by:", value)
                    await new Promise((resolve) => setTimeout(resolve, 500))
                    break

                case "wait":
                    await new Promise((resolve) => setTimeout(resolve, duration || 1000))
                    console.log("[v0] Waited for:", duration, "ms")
                    break

                case "hover":
                    if (target) {
                        const element = document.querySelector(`[data-v-id="${target}"]`)
                        if (element) {
                            const event = new MouseEvent("mouseover", { bubbles: true })
                            element.dispatchEvent(event)
                            console.log("[v0] Hovered over element:", target)
                        }
                    }
                    break

                default:
                    console.log("[v0] Unknown action type:", type)
            }

            // Small delay between actions
            await new Promise((resolve) => setTimeout(resolve, 200))
        } catch (e) {
            console.error("[v0] Error executing action:", action, e)
        }
    }
}

// Listen for messages from popup or background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "GET_DOM") {
        try {
            const dom = getSimplifiedDOM()
            sendResponse({ success: true, dom: dom })
        } catch (e) {
            console.error("[v0] Error getting DOM:", e)
            sendResponse({ success: false, error: e.message })
        }
    } else if (request.type === "EXECUTE_ACTIONS") {
        try {
            executeActions(request.actions)
            sendResponse({ success: true })
        } catch (e) {
            console.error("[v0] Error executing actions:", e)
            sendResponse({ success: false, error: e.message })
        }
    }
})

console.log("[v0] Content script loaded")
