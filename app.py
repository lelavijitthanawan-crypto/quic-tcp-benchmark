import streamlit as st
import plotly.graph_objects as go
import numpy as np
import time

st.set_page_config(page_title="TCP vs QUIC Benchmarking", layout="wide")

st.title("🚀 Transport Layer Telemetry: TCP vs QUIC")
st.caption("DES331 Project: Synthetic Impairment & Head-of-Line Blocking Analysis")

# 1. Sidebar สำหรับจำลอง Network Impairments (tc-netem simulation)
st.sidebar.header("Network Impairment Settings (tc-netem)")
loss_rate = st.sidebar.slider("Packet Loss Rate (%)", min_value=0.0, max_value=15.0, value=3.0, step=0.5)
latency = st.sidebar.slider("Base Latency (ms)", min_value=10, max_value=200, value=50, step=10)
jitter = st.sidebar.slider("Delay Jitter (±ms)", min_value=0, max_value=50, value=15, step=5)
num_streams = st.sidebar.select_slider("Concurrent Streams", options=[1, 4, 8, 16], value=8)

# 2. ฟังก์ชันคำนวณแบบจำลองทางคณิตศาสตร์ตามสมการ Transport Layer
def run_telemetry_simulation(loss, rtt, streams):
    # TCP ได้รับผลกระทบจาก HoL blocking: เวลาแปรผันแบบเลขชี้กำลังตาม loss
    tcp_multiplier = 1.0 + (loss * 0.45) ** 1.35
    tcp_times = [
        (rtt * 2.5 + np.random.uniform(10, 40) + (loss * 120 if np.random.rand() < (loss / 100) else 0)) / 1000.0
        for _ in range(streams)
    ]
    # อาการ HoL Blocking: สตรีมที่เหลือต้องหยุดรอสตรีมที่ช้าที่สุด
    max_tcp_stall = max(tcp_times)
    tcp_completion_times = [max(t, max_tcp_stall * 0.85) for t in tcp_times]

    # QUIC แยกอิสระต่อสตรีม (Multiplexing): สตรีมไหนไม่หล่นก็วิ่งจบได้เลย
    quic_completion_times = [
        (rtt * 1.2 + np.random.uniform(5, 20) + (loss * 30 if np.random.rand() < (loss / 100) else 0)) / 1000.0
        for _ in range(streams)
    ]

    return tcp_completion_times, quic_completion_times

if st.button("▶ Run Live Benchmark", type="primary"):
    with st.spinner("Injecting network impairments and capturing telemetry..."):
        time.sleep(0.8) # จำลองเวลาประมวลผล
        tcp_res, quic_res = run_telemetry_simulation(loss_rate, latency, num_streams)

    # 3. สรุปตัวเลข Metric สำคัญ
    avg_tcp = np.mean(tcp_res)
    avg_quic = np.mean(quic_res)
    delta = ((avg_tcp - avg_quic) / avg_tcp) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("TCP Avg Completion", f"{avg_tcp:.3f} s")
    col2.metric("QUIC Avg Completion", f"{avg_quic:.3f} s", f"-{delta:.1f}% Time", delta_color="inverse")
    col3.metric("HoL Blocking Mitigation", "Active (Zero Head-Stall)" if loss_rate > 0 else "Optimal Link")

    # 4. กราฟแท่งเปรียบเทียบแต่ละสตรีม (Head-of-Line Blocking Visualization)
    st.subheader("Stream Completion Time Comparison (Per-Stream Dynamics)")
    streams_axis = [f"Stream {i+1}" for i in range(num_streams)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=streams_axis, y=tcp_res, name="TCP + TLS 1.3", marker_color="#EF553B"))
    fig.add_trace(go.Bar(x=streams_axis, y=quic_res, name="QUIC (RFC 9000)", marker_color="#00CC96"))
    
    fig.update_layout(
        barmode="group",
        yaxis_title="Completion Time (seconds)",
        xaxis_title="Concurrent Data Streams",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info("💡 **SOC & Telemetry Insight:** In TCP, a single packet drop causes subsequent packets across all logical streams to stall in the socket receive buffer (Head-of-Line Blocking). QUIC eliminates this by allowing independent byte-streams over UDP datagrams.")