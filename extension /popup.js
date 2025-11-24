let isRecording = false
let mediaRecorder = null
let audioChunks = []
let currentTabId = null

const recordBtn = document.getElementById("recordBtn")
const stopBtn = document.getElementById("stopBtn")
const resetBtn = document.getElementById("resetBtn")
const statusIndicator = document.getElementById("statusIndicator")
const statusText = document.getElementById("statusText")
const infoSection = document.getElementById("infoSection")
const errorSection = document.getElementById("errorSection")

// Declare chrome variable
const chrome = window.chrome

// Update status indicator
function updateStatus(status, type = "idle") {
    const dot = statusIndicator.querySelector(".status-dot")
    const text = statusIndicator.querySelector(".status-text")

    dot.className = `status-dot ${type}`
    text.textContent = status
}

// Start recording
recordBtn.addEventListener("click", async () => {
    try {
        // Get current tab
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
        currentTabId = tab.id

        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })

        // Set up media recorder
        mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" })
        audioChunks = []

        mediaRecorder.addEventListener("dataavailable", (event) => {
            audioChunks.push(event.data)
        })

        mediaRecorder.addEventListener("stop", async () => {
            await handleRecordingStop()
        })

        mediaRecorder.start()
        isRecording = true

        // Update UI
        recordBtn.style.display = "none"
        stopBtn.style.display = "flex"
        stopBtn.disabled = false
        updateStatus("Listening...", "recording")
        errorSection.style.display = "none"

        console.log("[v0] Recording started")
    } catch (error) {
        console.error("[v0] Error starting recording:", error)
        showError("Microphone access denied. Please allow microphone access.")
        updateStatus("Ready", "error")
    }
})

// Stop recording
stopBtn.addEventListener("click", () => {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop()
        isRecording = false
        stopBtn.disabled = true
        updateStatus("Processing...", "processing")
    }
})

// Handle recording stop
async function handleRecordingStop() {
    try {
        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: "audio/webm" })

        // Convert to base64
        const reader = new FileReader()
        reader.onload = async (e) => {
            const base64Audio = e.target.result.split(",")[1]

            // Get DOM from active tab
            const domResponse = await chrome.tabs.sendMessage(currentTabId, {
                type: "GET_DOM",
            })

            if (!domResponse.success) {
                showError("Failed to get page DOM.")
                resetUI()
                return
            }

            const dom = domResponse.dom

            // Send to backend
            updateStatus("Thinking...", "processing")
            console.log("[v0] Sending to backend...")

            const backendResponse = await new Promise((resolve) => {
                chrome.runtime.sendMessage(
                    {
                        type: "SEND_TO_BACKEND",
                        audio: base64Audio,
                        dom: dom,
                        tabId: currentTabId,
                    },
                    (response) => {
                        resolve(response)
                    },
                )
            })

            if (!backendResponse.success) {
                showError(`Backend error: ${backendResponse.error}`)
                resetUI()
                return
            }

            // Display results
            updateStatus("Executing...", "processing")
            displayResults(backendResponse)

            // Play audio response
            if (backendResponse.audioResponse) {
                const audioData = Uint8Array.from(atob(backendResponse.audioResponse), (c) => c.charCodeAt(0))
                const audioBlob = new Blob([audioData], { type: "audio/mp3" })
                const audioUrl = URL.createObjectURL(audioBlob)
                const audio = new Audio(audioUrl)
                audio.play().catch((e) => console.error("[v0] Error playing audio:", e))
            }

            // Wait a bit then reset
            setTimeout(() => {
                updateStatus("Complete", "success")
                setTimeout(() => {
                    resetUI()
                }, 2000)
            }, 2000)
        }

        reader.readAsDataURL(audioBlob)
    } catch (error) {
        console.error("[v0] Error handling recording stop:", error)
        showError(`Error: ${error.message}`)
        resetUI()
    }
}

// Display results
function displayResults(response) {
    document.getElementById("transcriptText").textContent = response.transcript || "N/A"
    document.getElementById("thoughtText").textContent = response.thought || "N/A"

    const actionsText = response.actions ? JSON.stringify(response.actions, null, 2) : "No actions"
    document.getElementById("actionsText").textContent = actionsText

    infoSection.style.display = "block"
    errorSection.style.display = "none"
}

// Show error
function showError(message) {
    document.getElementById("errorText").textContent = message
    errorSection.style.display = "block"
    infoSection.style.display = "none"
}

// Reset UI
function resetUI() {
    recordBtn.style.display = "flex"
    stopBtn.style.display = "none"
    stopBtn.disabled = true
    updateStatus("Ready", "idle")
    infoSection.style.display = "none"
    errorSection.style.display = "none"
}

// Handle reset button
resetBtn.addEventListener("click", resetUI)

// Initialize
console.log("[v0] Popup script loaded")
