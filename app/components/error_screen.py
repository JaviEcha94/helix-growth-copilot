import streamlit as st

from app.i18n import t


def render_error_screen(on_retry) -> None:
    T = t(st.session_state["lang"])
    error_detail = st.session_state.get("last_error") or ""

    st.markdown(
        '<style>.st-key-error_wrap{ max-width:520px; margin:60px auto; text-align:center; }</style>',
        unsafe_allow_html=True,
    )
    with st.container(key="error_wrap"):
        st.markdown('<div class="helix-error-icon">⚠️</div>', unsafe_allow_html=True)
        st.markdown(f"<h2 style='font-size:22px;margin:0 0 8px;'>{T['errorTitle']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94A3B8;font-size:14px;line-height:1.5;'>{T['errorMsg']}</p>", unsafe_allow_html=True)
        if error_detail:
            st.caption(f"Detalle técnico: {error_detail}")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _, mid, _ = st.columns([1, 1, 1])
        with mid:
            if st.button(T["retry"], key="retry_btn", type="primary", use_container_width=True):
                on_retry()
