/* ============================================================
   DevTrack — core/api.js
   Small fetch-based REST client. Exposes the global `API`
   object used by all feature scripts.
   ============================================================ */

const API = {
    async request(url, options = {}) {
        const config = {
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            ...options,
        };
        if (config.body && typeof config.body !== "string") {
            config.body = JSON.stringify(config.body);
        }
        const res = await fetch(url, config);
        if (res.status === 204) return null;
        let data = null;
        try {
            data = await res.json();
        } catch (_) {
            data = null;
        }
        if (!res.ok) {
            const message = (data && data.error) ? data.error : `Request failed (${res.status})`;
            throw new Error(message);
        }
        return data;
    },

    get(url) {
        return this.request(url);
    },
    post(url, body) {
        return this.request(url, { method: "POST", body });
    },
    put(url, body) {
        return this.request(url, { method: "PUT", body });
    },
    del(url) {
        return this.request(url, { method: "DELETE" });
    },
};