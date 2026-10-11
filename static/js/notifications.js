/**
 * Real-time Health Reminder & Notification Engine
 * - Web Audio API synthesized alert chime
 * - Desktop Browser Notifications API integration
 * - In-app Toast alerts with direct completion & snooze
 * - Notification bell center sync
 */

class NotificationEngine {
    constructor() {
        this.pollInterval = 20000; // Check every 20s
        this.audioCtx = null;
        this.init();
    }

    init() {
        this.setupPermissionBanner();
        this.setupMarkAllRead();
        // Initial check after short delay
        setTimeout(() => this.checkDueReminders(), 1500);
        // Periodic check
        setInterval(() => this.checkDueReminders(), this.pollInterval);
    }

    // Synthesized pleasant medical reminder chime using Web Audio API
    playChime() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            if (!this.audioCtx) {
                this.audioCtx = new AudioContext();
            }
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }

            const now = this.audioCtx.currentTime;

            // First chime tone (E5 - 659 Hz)
            const osc1 = this.audioCtx.createOscillator();
            const gain1 = this.audioCtx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(659.25, now);
            gain1.gain.setValueAtTime(0.2, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
            osc1.connect(gain1);
            gain1.connect(this.audioCtx.destination);
            osc1.start(now);
            osc1.stop(now + 0.5);

            // Second higher chime tone (B5 - 987 Hz)
            const osc2 = this.audioCtx.createOscillator();
            const gain2 = this.audioCtx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(987.77, now + 0.15);
            gain2.gain.setValueAtTime(0.25, now + 0.15);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.8);
            osc2.connect(gain2);
            gain2.connect(this.audioCtx.destination);
            osc2.start(now + 0.15);
            osc2.stop(now + 0.8);
        } catch (e) {
            console.log("Audio chime playback blocked or not supported:", e);
        }
    }

    setupPermissionBanner() {
        const banner = document.getElementById('desktopNotifBanner');
        const enableBtn = document.getElementById('enableNotifBtn');

        if (!banner || !enableBtn) return;

        if ("Notification" in window) {
            if (Notification.permission === "default") {
                banner.classList.remove('d-none');
            }

            enableBtn.addEventListener('click', () => {
                Notification.requestPermission().then(permission => {
                    if (permission === "granted") {
                        banner.classList.add('d-none');
                        new Notification("Notifications Enabled", {
                            body: "You will now receive desktop alerts for scheduled medicines and health reminders.",
                            icon: "/static/img/pulse.png"
                        });
                    } else {
                        banner.classList.add('d-none');
                    }
                });
            });
        }
    }

    setupMarkAllRead() {
        const btn = document.getElementById('markAllReadBtn');
        if (btn) {
            btn.addEventListener('click', () => {
                fetch('/api/notifications/mark-read', { method: 'POST' })
                    .then(res => res.json())
                    .then(() => {
                        const badge = document.getElementById('notifBadge');
                        if (badge) badge.classList.add('d-none');
                        const list = document.getElementById('notifList');
                        if (list) {
                            list.innerHTML = '<li class="text-center text-muted small py-3">No unread notifications</li>';
                        }
                    });
            });
        }
    }

    checkDueReminders() {
        fetch('/api/notifications/check-due')
            .then(res => res.json())
            .then(data => {
                if (data.status !== 'ok') return;

                // Update unread count badge & dropdown
                const badge = document.getElementById('notifBadge');
                const list = document.getElementById('notifList');

                if (badge && list) {
                    if (data.unread_count > 0) {
                        badge.textContent = data.unread_count;
                        badge.classList.remove('d-none');

                        list.innerHTML = data.unread_notifications.map(n => `
                            <li class="notif-item border-bottom mb-1 pb-1">
                                <div class="d-flex align-items-center justify-content-between">
                                    <strong class="small text-teal">${n.title}</strong>
                                </div>
                                <div class="text-muted small text-truncate">${n.message}</div>
                            </li>
                        `).join('');
                    } else {
                        badge.classList.add('d-none');
                        list.innerHTML = '<li class="text-center text-muted small py-3">No unread notifications</li>';
                    }
                }

                // If new due notifications arrived this cycle, play chime & trigger desktop/toast
                if (data.new_notifications && data.new_notifications.length > 0) {
                    this.playChime();

                    data.new_notifications.forEach(item => {
                        this.showDesktopNotification(item);
                        this.showInAppToast(item);
                    });
                }
            })
            .catch(err => console.error("Notification poll failed:", err));
    }

    showDesktopNotification(item) {
        if ("Notification" in window && Notification.permission === "granted") {
            const notif = new Notification(item.title, {
                body: item.message,
                tag: `reminder-${item.reminder_id}`,
                requireInteraction: true
            });
            notif.onclick = () => {
                window.focus();
                window.location.href = `/reminders/`;
            };
        }
    }

    showInAppToast(item) {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toastId = 'toast-' + Date.now() + Math.random().toString(36).substr(2, 4);
        const toastEl = document.createElement('div');
        toastEl.className = 'toast show border-0 shadow-lg mb-2 rounded-3';
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.id = toastId;

        toastEl.innerHTML = `
            <div class="toast-header bg-teal text-white rounded-top-3">
                <i class="fa-solid fa-bell me-2"></i>
                <strong class="me-auto">${item.title}</strong>
                <small class="text-light">${item.time || 'Now'}</small>
                <button type="button" class="btn-close btn-close-white ms-2" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body bg-white rounded-bottom-3">
                <p class="mb-2 text-dark small">${item.message}</p>
                <div class="d-flex gap-2">
                    <form action="/reminders/${item.reminder_id}/complete" method="POST" class="d-inline">
                        <button type="submit" class="btn btn-sm btn-success px-2 py-1 small">
                            <i class="fa-solid fa-check me-1"></i> Mark Done
                        </button>
                    </form>
                    <form action="/reminders/${item.reminder_id}/snooze" method="POST" class="d-inline">
                        <input type="hidden" name="minutes" value="10">
                        <button type="submit" class="btn btn-sm btn-outline-secondary px-2 py-1 small">
                            <i class="fa-solid fa-clock me-1"></i> Snooze 10m
                        </button>
                    </form>
                </div>
            </div>
        `;

        container.appendChild(toastEl);
        // Automatically dismiss toast after 30 seconds if not clicked
        setTimeout(() => {
            if (document.getElementById(toastId)) {
                toastEl.classList.remove('show');
                setTimeout(() => toastEl.remove(), 400);
            }
        }, 30000);
    }
}

// Instantiate engine when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.healthNotifications = new NotificationEngine();
});
