"""
Interactive Demonstration of tkblend.prismtk: Declarative, CSS-styled, State-Driven UI Engine.
"""

import tkblend.prismtk as prism
import tkblend as tb

TEMPLATE = """
<box class="window-root">
    <box class="card {status}">
        <box class="header-row">
            <box class="avatar">
                <circle class="status-indicator" />
            </box>
            <box class="header-text">
                <text class="title">{username}</text>
                <text class="subtitle">{role} • {status == 'online' ? 'Online' : 'Busy'}</text>
            </box>
        </box>

        <box class="stats-box">
            <text class="stats-label">Task Completion</text>
            <progress value="{progress}" max="100" class="progress-bar" />
            <text class="stats-pct">{progress}% Completed</text>
        </box>

        <box class="button-row">
            <button class="btn btn-primary" on_click="increment_progress">+10% Progress</button>
            <button class="btn btn-secondary" on_click="toggle_status">Toggle Status</button>
        </box>
    </box>
</box>
"""

CSS = """
.window-root {
    background: #0f111a;
    padding: 30px;
    align-items: center;
    justify-content: center;
}

.card {
    width: 380px;
    background: #1a1c29;
    border: 1px solid #2a2e42;
    border-radius: 16px;
    padding: 24px;
    gap: 16px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.card:hover {
    border: 1px solid #3b82f6;
    box-shadow: 0 12px 36px rgba(59, 130, 246, 0.2);
}

.card.online {
    border: 1px solid #10b981;
}

.card.busy {
    border: 1px solid #f59e0b;
}

.header-row {
    flex-direction: row;
    align-items: center;
    gap: 14px;
}

.avatar {
    width: 46px;
    height: 46px;
    background: #25293d;
    border-radius: 23px;
    align-items: center;
    justify-content: center;
}

.status-indicator {
    width: 14px;
    height: 14px;
    background: #10b981;
}

.card.busy .status-indicator {
    background: #f59e0b;
}

.header-text {
    gap: 4px;
}

.title {
    color: #ffffff;
    font-size: 17px;
    text-align: left;
}

.subtitle {
    color: #94a3b8;
    font-size: 13px;
    text-align: left;
}

.stats-box {
    background: #141622;
    border-radius: 10px;
    padding: 12px;
    gap: 8px;
}

.stats-label {
    color: #cbd5e1;
    font-size: 12px;
    text-align: left;
}

.stats-pct {
    color: #60a5fa;
    font-size: 12px;
    text-align: right;
}

.progress-bar {
    height: 8px;
    border-radius: 4px;
    background: #25293d;
    color: #3b82f6;
}

.button-row {
    flex-direction: row;
    gap: 12px;
}

.btn {
    height: 38px;
    border-radius: 8px;
    font-size: 13px;
}

.btn-primary {
    background: #3b82f6;
    color: #ffffff;
}

.btn-primary:hover {
    background: #2563eb;
}

.btn-primary:active {
    background: #1d4ed8;
}

.btn-secondary {
    background: #25293d;
    border: 1px solid #3b4261;
    color: #e2e8f0;
}

.btn-secondary:hover {
    background: #313752;
}

.btn-secondary:active {
    background: #1e2233;
}
"""


def main():
    app = prism.App(
        title="PrismTK - Declarative Vector UI",
        width=480,
        height=380,
        template=TEMPLATE,
        css=CSS,
        state={
            "username": "Mateus",
            "role": "Systems Architect",
            "status": "online",
            "progress": 65.0,
        }
    )

    @app.action("increment_progress")
    def on_increment():
        curr = app.state.progress
        app.state.progress = 0.0 if curr >= 100.0 else min(100.0, curr + 10.0)

    @app.action("toggle_status")
    def on_toggle_status():
        app.state.status = "busy" if app.state.status == "online" else "online"

    app.run()


if __name__ == "__main__":
    main()
