import os

# Define the new content block
NEW_ARCH_HTML = r'''    <section class="arch-section">
        <span class="section-title">The Architecture</span>

        <!-- INTERACTIVE SVG OVERLAY -->
        <div id="arch-container" style="position:relative;">
            <!-- SVG Layer -->
            <svg id="arch-svg" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:0; overflow:visible;"></svg>
            
            <!-- Grid Layer -->
            <div class="arch-grid" id="arch-grid-container" style="position:relative; z-index:1;">
                <!-- Step 1 -->
                <div class="arch-card" id="node-1">
                    <span class="step-num">01</span>
                    <div class="arch-content">
                        <h3>Multi-Source Ingestion</h3>
                        <p>Parallel <code>pw.io.connectors</code> ingest data from OPML, GNews, and Twitter. Data is normalized instantaneously into a <code>pw.Table</code>.</p>
                        <span class="code-tag">pw.io.connectors</span>
                    </div>
                </div>

                <!-- Step 2 -->
                <div class="arch-card" id="node-2">
                    <span class="step-num">02</span>
                    <div class="arch-content">
                        <h3>Unified Stream</h3>
                        <p>Live items are merged into a single infinite table. The Rust engine handles backpressure and consistency automatically.</p>
                        <span class="code-tag">pw.Table</span>
                    </div>
                </div>

                <!-- Step 3 -->
                <div class="arch-card" id="node-3">
                    <span class="step-num">03</span>
                    <div class="arch-content">
                        <h3>Live Embedding</h3>
                        <p>Incoming text is embedded on-the-fly using <code>pw.xpacks.llm.embedders</code>, creating a dynamic 384-dimensional semantic map.</p>
                        <span class="code-tag">pw.xpacks.llm.embedders</span>
                    </div>
                </div>

                <!-- Step 4 -->
                <div class="arch-card" id="node-4">
                    <span class="step-num">04</span>
                    <div class="arch-content">
                        <h3>Semantic Indexing</h3>
                        <p>We use <code>pw.xpacks.llm</code> to maintain a Live KNN Index, allowing for search by "meaning" rather than just keywords.</p>
                        <span class="code-tag">pw.xpacks.llm</span>
                    </div>
                </div>

                <!-- Step 5 -->
                <div class="arch-card" id="node-5">
                    <span class="step-num">05</span>
                    <div class="arch-content">
                        <h3>Freshness Filtering</h3>
                        <p><code>pw.temporal.sliding</code> windows strictly filter for breaking news clusters, ensuring AI reasons on the "Now".</p>
                        <span class="code-tag">pw.temporal.sliding</span>
                    </div>
                </div>

                <!-- Step 6 -->
                <div class="arch-card" id="node-6">
                    <span class="step-num">06</span>
                    <div class="arch-content">
                        <h3>Context Construction</h3>
                        <p><code>pw.io.deduplicate</code> ensures the context window is filled with unique, high-value information, not duplicates.</p>
                        <span class="code-tag">pw.io.deduplicate</span>
                    </div>
                </div>

                <!-- Step 7 -->
                <div class="arch-card" id="node-7">
                    <span class="step-num">07</span>
                    <div class="arch-content">
                        <h3>LLM Synthesis</h3>
                        <p>Gemini 1.5 analyzes the retrieved <code>pw.Table</code> context rows to generate an executive summary in milliseconds.</p>
                        <span class="code-tag">query_gemini()</span>
                    </div>
                </div>

                <!-- Step 8 -->
                <div class="arch-card" id="node-8">
                    <span class="step-num">08</span>
                    <div class="arch-content">
                        <h3>Client Hydration</h3>
                        <p>FastAPI streams the ready-state JSON to the UI, rendering updates instantly.</p>
                        <span class="code-tag">app_pathway.py</span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // DYNAMIC DATA FLOW ENGINE
            (function() {
                const svg = document.getElementById('arch-svg');
                const container = document.getElementById('arch-container');
                let nodes = [];

                function initNodes() {
                    nodes = [];
                    for(let i=1; i<=8; i++) {
                        const el = document.getElementById(`node-${i}`);
                        if(el) nodes.push(el);
                    }
                }

                function drawConnections() {
                    if(!nodes.length) initNodes();
                    if(!svg || !container) return;

                    // resize svg
                    svg.setAttribute('width', container.offsetWidth);
                    svg.setAttribute('height', container.offsetHeight);
                    svg.innerHTML = ''; // Clear

                    // DEFN: Marker
                    const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
                    svg.appendChild(defs);

                    const cRect = container.getBoundingClientRect();

                    // Draw paths between i and i+1
                    for(let i=0; i<nodes.length-1; i++) {
                        const n1 = nodes[i];
                        const n2 = nodes[i+1];
                        const r1 = n1.getBoundingClientRect();
                        const r2 = n2.getBoundingClientRect();
                        
                        // Centers relative to container
                        const x1 = (r1.left + r1.right)/2 - cRect.left;
                        const y1 = (r1.top + r1.bottom)/2 - cRect.top;
                        const x2 = (r2.left + r2.right)/2 - cRect.left;
                        const y2 = (r2.top + r2.bottom)/2 - cRect.top;

                        // Create Path
                        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
                        let d = `M ${x1} ${y1}`;
                        
                        // If same row (approx)
                        if (Math.abs(y1 - y2) < 50) {
                            d += ` L ${x2} ${y2}`;
                        } else {
                            // Curve
                            const cp1x = x1;
                            const cp1y = y1 + (y2-y1)/2;
                            const cp2x = x2;
                            const cp2y = y1 + (y2-y1)/2;
                            d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${x2} ${y2}`;
                        }

                        path.setAttribute("d", d);
                        path.setAttribute("stroke", "#e0e0e0"); 
                        path.setAttribute("stroke-width", "4");
                        path.setAttribute("fill", "none");
                        path.setAttribute("stroke-linecap", "round");
                        path.setAttribute("id", `path-${i}`);
                        svg.appendChild(path);

                        // Animated Particle
                        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                        circle.setAttribute("r", "6");
                        circle.setAttribute("fill", "#00b85c");
                        
                        // Flow Animation
                        const animate = document.createElementNS("http://www.w3.org/2000/svg", "animateMotion");
                        animate.setAttribute("dur", "1.5s");
                        animate.setAttribute("repeatCount", "indefinite");
                        animate.setAttribute("begin", `${i * 0.3}s`); // Fast flow
                        
                        const mpath = document.createElementNS("http://www.w3.org/2000/svg", "mpath");
                        mpath.setAttributeNS("http://www.w3.org/1999/xlink", "href", `#path-${i}`);
                        
                        animate.appendChild(mpath);
                        circle.appendChild(animate);
                        svg.appendChild(circle);
                    }
                }

                // Initial Draw & Listeners
                setTimeout(drawConnections, 500);
                setTimeout(drawConnections, 2000); 
                window.addEventListener('resize', drawConnections);

                // CSS for Pulse
                const style = document.createElement('style');
                style.innerHTML = `
                    @keyframes nodePulse {
                        0% { border-color: #000; box-shadow: 5px 5px 0px #555; }
                        50% { border-color: #00b85c; box-shadow: 0 0 15px #00b85c; }
                        100% { border-color: #000; box-shadow: 5px 5px 0px #555; }
                    }
                    .arch-card.active-pulse {
                        animation: nodePulse 0.6s ease-out;
                    }
                `;
                document.head.appendChild(style);

                // Simulation loop
                let activeNode = 0;
                setInterval(() => {
                    if (nodes.length === 0) initNodes();
                    if (activeNode < nodes.length) {
                        nodes[activeNode].classList.add('active-pulse');
                        setTimeout((n) => n.classList.remove('active-pulse'), 600, nodes[activeNode]);
                        activeNode++;
                    } else {
                        activeNode = 0;
                    }
                }, 1500 / 2);
            })();
        </script>
    </section>'''

TARGET_FILE = 'frontend/landing.html'

with open(TARGET_FILE, 'r') as f:
    content = f.read()

# Locate the markers
start_marker = '<!-- ARCHITECTURE GRID -->'
end_marker = '<!-- VERGE STYLE FOOTER -->'

# Find indices
start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("❌ Critical Error: Could not find markers in file.")
    exit(1)

# Construct new file content
# Keep `start_marker` (optional, but good for structure), then insert NEW_ARCH_HTML, then `end_marker`
new_content = content[:start_idx] + "<!-- ARCHITECTURE GRID -->\n" + NEW_ARCH_HTML + "\n\n    " + content[end_idx:]

with open(TARGET_FILE, 'w') as f:
    f.write(new_content)

print("✅ Successfully updated landing.html architecture section.")
