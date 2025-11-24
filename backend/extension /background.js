const recordingState = {
    isRecording: false,
    tabId: null,
    audioChunks: [],
}

// Declare chrome variable
const chrome = window.chrome

// Handle keyboard shortcut (Alt+V)
chrome.commands.onCommand.addListener((command) => {
    if (command === "toggle-recording") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]) {
                chrome.tabs.sendMessage(tabs[0].id, { type: "TOGGLE_RECORDING" })
            }
        })
    }
})

// Handle messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === "START_RECORDING") {
        recordingState.isRecording = true
        recordingState.tabId = sender.tab?.id
        recordingState.audioChunks = []
        console.log("[v0] Recording started")
        sendResponse({ success: true })
    } else if (request.type === "STOP_RECORDING") {
        recordingState.isRecording = false
        const audioChunks = recordingState.audioChunks
        recordingState.audioChunks = []
        console.log("[v0] Recording stopped, chunks:", audioChunks.length)
        sendResponse({ success: true, audioChunks: audioChunks })
    } else if (request.type === "ADD_AUDIO_CHUNK") {
        recordingState.audioChunks.push(request.chunk)
    } else if (request.type === "SEND_TO_BACKEND") {
        handleBackendRequest(request, sendResponse)
        return true // Keep channel open for async response
    }
})

// Send audio + DOM to backend
async function handleBackendRequest(request, sendResponse) {
    try {
        const { audio, dom, tabId } = request

        // Create FormData
        const formData = new FormData()

        // Convert base64 audio to Blob
        const byteCharacters = atob(audio)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const audioBlob = new Blob([byteArray], { type: "audio/webm" })

        formData.append("audio", audioBlob, "recording.webm")
        formData.append("dom_context", JSON.stringify(dom))

        console.log("[v0] Sending to backend:", {
            audioSize: audioBlob.size,
            domElements: dom.length,
        })

        // Send to backend
        const response = await fetch("http://localhost:8000/api/v1/voice/command", {
            method: "POST",
            body: formData,
        })

        if (!response.ok) {
            throw new Error(`Backend error: ${response.status}`)
        }

        const result = await response.json()

        console.log("[v0] Backend response:", result)

        // Send actions to content script
        if (tabId && result.actions) {
            chrome.tabs
                .sendMessage(tabId, {
                    type: "EXECUTE_ACTIONS",
                    actions: result.actions,
                })
                .catch((e) => console.error("[v0] Error sending actions:", e))
        }

        sendResponse({
            success: true,
            transcript: result.transcript,
            thought: result.thought,
            speakBefore: result.speak_before,
            actions: result.actions,
            audioResponse: result.audio_response_base64,
            audioLogUrl: result.audio_log_url,
        })
    } catch (error) {
        console.error("[v0] Backend request error:", error)
        sendResponse({
            success: false,
            error: error.message,
        })
    }
}

console.log("[v0] Background service worker loaded")