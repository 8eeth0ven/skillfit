---
name: voice-dictation-setup
description: Help configure optional local Whisper dictation into terminals and other apps, with language, hotkey and CPU or GPU checks.
---

# Voice dictation setup

Read [the setup note](../../../knowledge/voice-dictation.md) and the chosen
tool's current upstream instructions. Dictation is independent of Mr. Mak's
conversational voice assistant. Keep the two workflows distinct.

Check the operating system, microphone, language and available hardware. Choose
a local model that fits the machine. Verify the tool's defaults: a configured
language or GPU build flag may need changing for this user. Do not promise that
a build compiled with CUDA will run without the required runtime.

Choose a hotkey with the user before rebinding an existing shortcut. Test a short
sentence in a plain text field, then in a terminal without submitting it. Check
mixed technical vocabulary, silence and quick repeated recordings. Confirm that
the next recording starts reliably after a failure.

Leave optional cloud formatting disabled unless requested. If enabled, explain
which text goes to the selected provider and use the user's own credentials.
Store only reusable setup notes in this project, not voice history or account
settings. Do not restart Mr. Mak to configure a separate dictation application.
