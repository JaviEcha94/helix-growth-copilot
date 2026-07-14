import streamlit as st

from app.i18n import t
from app.state import persist, toast
from app.validation import CARD_ICONS, CARD_ORDER, FIELD_KEYS, FIELD_TYPES, SAMPLE, validate_value


def _load_sample() -> None:
    for key, value in SAMPLE.items():
        st.session_state["form"][key] = value
        st.session_state[f"field_{key}"] = value
    st.session_state["expanded"] = {c: True for c in CARD_ORDER}
    st.session_state["empty_warning"] = False
    if not st.session_state.get("store_name"):
        st.session_state["store_name"] = "TiendaNova"
        st.session_state["field_store_name"] = "TiendaNova"
    if not st.session_state.get("period"):
        from datetime import date

        st.session_state["period"] = date.today().strftime("%B %Y")
        st.session_state["field_period"] = st.session_state["period"]
    persist()
    toast(t(st.session_state["lang"])["toastSample"])


def _dismiss_coachmark() -> None:
    st.session_state["coachmark_seen"] = True
    st.session_state["show_coachmark"] = False
    persist()


def _sync_field(key: str) -> None:
    st.session_state["form"][key] = st.session_state[f"field_{key}"]


def _card_status(card_id: str, T: dict) -> tuple[str, bool]:
    keys = FIELD_KEYS[card_id]
    filled = sum(1 for k in keys if st.session_state["form"].get(k))
    complete = filled == len(keys)
    if complete:
        return T["statusComplete"], True
    if filled > 0:
        return f"{filled}/{len(keys)}", False
    return T["statusPending"], False


def _render_card(card_id: str, T: dict) -> None:
    cdef = T["cards"][card_id]
    keys = FIELD_KEYS[card_id]
    types = FIELD_TYPES[card_id]
    status_text, _complete = _card_status(card_id, T)

    label = f"{CARD_ICONS[card_id]}  **{cdef['title']}** — {cdef['desc']}   `{status_text}`"
    st.markdown(
        f'<style>.st-key-card_{card_id}{{'
        'background:var(--surface) !important; backdrop-filter:blur(12px); border:1px solid var(--border) !important;'
        'border-radius:18px !important; box-shadow:inset 0 1px 0 rgba(255,255,255,.06), 0 0 20px rgba(37,99,235,.06) !important;'
        'overflow:hidden;'
        "}}"
        f'.st-key-card_{card_id} [data-testid="stExpanderDetails"]{{ border-top:1px solid rgba(255,255,255,.06); }}'
        f'.st-key-card_{card_id} summary{{ padding:14px 18px !important; }}'
        "</style>",
        unsafe_allow_html=True,
    )
    with st.expander(label, expanded=st.session_state["expanded"].get(card_id, False), key=f"card_{card_id}"):
        cols = st.columns(2)
        for i, field in enumerate(cdef["fields"]):
            key = keys[i]
            ftype = types[i]
            with cols[i % 2]:
                value = st.text_input(
                    field["label"], value=st.session_state["form"].get(key, ""),
                    placeholder=field["ph"], help=field.get("tip") or None,
                    key=f"field_{key}", on_change=_sync_field, args=(key,),
                )
                err_key = validate_value(ftype, value)
                if value and not err_key:
                    st.markdown('<span style="color:#22C55E;font-size:12px;">✓ OK</span>', unsafe_allow_html=True)
                elif value and err_key:
                    st.markdown(f'<span style="color:#EF4444;font-size:11.5px;">{T[err_key]}</span>', unsafe_allow_html=True)


def _any_field_filled() -> bool:
    return any(bool(v) for v in st.session_state["form"].values())


def render_input_screen(on_generate) -> None:
    T = t(st.session_state["lang"])

    st.markdown(f'<div class="helix-eyebrow">{T["eyebrow"]}</div>', unsafe_allow_html=True)
    st.markdown(f"<h1 style='font-size:31px;margin:0 0 8px;'>{T['inputTitle']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#94A3B8;font-size:14.5px;max-width:660px;'>{T['inputSub']}</p>", unsafe_allow_html=True)
    st.markdown("".join(f'<span class="helix-chip">{c}</span>' for c in T["chips"]), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state["store_name"] = st.text_input(
            T["storeNameLabel"], value=st.session_state.get("store_name", ""),
            placeholder="TiendaNova", key="field_store_name",
        )
    with c2:
        st.session_state["period"] = st.text_input(
            T["periodLabel"], value=st.session_state.get("period", ""),
            placeholder="Julio 2026", key="field_period",
        )

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    for card_id in CARD_ORDER:
        _render_card(card_id, T)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    if st.session_state["empty_warning"]:
        st.markdown(
            f"""<div role="alert" style="display:flex;gap:12px;background:rgba(249,115,22,.09);
            border:1px solid rgba(249,115,22,.38);border-radius:12px;padding:13px 16px;max-width:540px;margin:0 auto 15px;">
            <span style="font-size:18px;">⚠️</span>
            <div><div style="font-weight:600;font-size:13.5px;">{T['emptyTitle']}</div>
            <div style="font-size:12.5px;color:#94A3B8;margin-top:2px;">{T['emptyMsg']}</div></div></div>""",
            unsafe_allow_html=True,
        )

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        if st.button(f"⚡ {T['ctaGenerate']}", key="generate_btn", type="primary", use_container_width=True):
            if not _any_field_filled():
                st.session_state["empty_warning"] = True
                st.rerun()
            else:
                on_generate()

    b1, b2, b3 = st.columns([1, 0.15, 1.4])
    with b1:
        st.button(T["loadSample"], key="load_sample_btn", on_click=_load_sample, use_container_width=True)
    with b3:
        st.caption(T["estimate"])

    if st.session_state["show_coachmark"]:
        cm1, cm2 = st.columns([3, 1])
        with cm1:
            st.markdown(f'<div class="helix-coachmark">{T["coachmarkText"]}</div>', unsafe_allow_html=True)
        with cm2:
            st.button(T["coachmarkDismiss"], key="dismiss_coachmark", on_click=_dismiss_coachmark)

    persist()
