typebot_iframe_html = """
<iframe
  src="https://viewer.typebot.io/basic-chat-gpt-133605h"
  style="border: none; width: 100%; height: 600px;"
></iframe>
"""

typebot_js_html = """
<div id="typebot-bubble-container"></div>
<script type="module">
  import Typebot from 'https://cdn.jsdelivr.net/npm/@typebot.io/js@0.2/dist/web.js';
  Typebot.initBubble({
    typebot: "basic-chat-gpt-133605h",
    container: "#typebot-bubble-container",
    bubble: true
  });
</script>
"""