import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Palette (validated categorical + chrome tokens, light mode)
# ---------------------------------------------------------------------------
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100",
    "#e87ba4", "#008300", "#4a3aa7", "#e34948",
)
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

st.set_page_config(page_title="Oscar Awards Dashboard", page_icon="🏆", layout="wide")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("the_oscar_award.csv")
    df["winner"] = df["winner"].astype(str).str.strip().str.lower() == "true"
    df["name"] = df["name"].fillna("Unknown")
    df["film"] = df["film"].fillna("Unknown")
    df["canon_category"] = df["canon_category"].fillna(df["category"])
    return df


df = load_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

year_min, year_max = int(df["year_ceremony"].min()), int(df["year_ceremony"].max())
year_range = st.sidebar.slider(
    "Ano da cerimônia", min_value=year_min, max_value=year_max,
    value=(year_min, year_max), step=1,
)

categories = sorted(df["canon_category"].unique())
selected_categories = st.sidebar.multiselect("Categoria", categories, default=[])

only_winners = st.sidebar.checkbox("Somente vencedores", value=False)

search = st.sidebar.text_input("Buscar por nome ou filme")

mask = df["year_ceremony"].between(*year_range)
if selected_categories:
    mask &= df["canon_category"].isin(selected_categories)
if only_winners:
    mask &= df["winner"]
if search:
    s = search.strip().lower()
    mask &= (
        df["name"].str.lower().str.contains(s, na=False)
        | df["film"].str.lower().str.contains(s, na=False)
    )

fdf = df[mask]

st.sidebar.markdown(f"**{len(fdf):,}** registros no filtro atual")

# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------
st.title("🏆 Oscar Awards Dashboard")
st.caption(
    f"Indicações e vencedores do Oscar entre {year_range[0]} e {year_range[1]} "
    "— dados da Academy Awards Database."
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Indicações", f"{len(fdf):,}")
k2.metric("Vitórias", f"{int(fdf['winner'].sum()):,}")
k3.metric("Filmes únicos", f"{fdf['film'].nunique():,}")
k4.metric("Indicados únicos", f"{fdf['name'].nunique():,}")
k5.metric("Categorias", f"{fdf['canon_category'].nunique():,}")

st.divider()


def styled_fig(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        height=height,
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=INK_SECONDARY, size=13),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(bgcolor="white", font_color=INK),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=GRID, tickfont=dict(color=INK_MUTED))
    fig.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=False, tickfont=dict(color=INK_MUTED))
    return fig


tab_overview, tab_people, tab_films, tab_data = st.tabs(
    ["Visão geral", "Indicados", "Filmes", "Explorar dados"]
)

# ---------------------------------------------------------------------------
# Tab 1: Overview
# ---------------------------------------------------------------------------
with tab_overview:
    col1, col2 = st.columns((2, 1))

    with col1:
        st.subheader("Indicações x vitórias por ano")
        by_year = (
            fdf.groupby("year_ceremony")
            .agg(nominations=("winner", "size"), wins=("winner", "sum"))
            .reset_index()
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=by_year["year_ceremony"], y=by_year["nominations"],
            name="Indicações", mode="lines", line=dict(color=BLUE, width=2),
        ))
        fig.add_trace(go.Scatter(
            x=by_year["year_ceremony"], y=by_year["wins"],
            name="Vitórias", mode="lines", line=dict(color=ORANGE, width=2),
        ))
        st.plotly_chart(styled_fig(fig), use_container_width=True)

    with col2:
        st.subheader("Top 10 categorias")
        top_cat = (
            fdf["canon_category"].value_counts().head(10).sort_values()
        )
        fig = go.Figure(go.Bar(
            x=top_cat.values, y=top_cat.index, orientation="h",
            marker_color=BLUE,
        ))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(styled_fig(fig, height=420), use_container_width=True)

    st.subheader("Indicações por década")
    fdf_decade = fdf.copy()
    fdf_decade["decade"] = (fdf_decade["year_ceremony"] // 10 * 10).astype(int).astype(str) + "s"
    by_decade = (
        fdf_decade.groupby("decade")
        .agg(nominations=("winner", "size"), wins=("winner", "sum"))
        .reset_index()
        .sort_values("decade")
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(x=by_decade["decade"], y=by_decade["nominations"], name="Indicações", marker_color=BLUE))
    fig.add_trace(go.Bar(x=by_decade["decade"], y=by_decade["wins"], name="Vitórias", marker_color=ORANGE))
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    st.plotly_chart(styled_fig(fig, height=380), use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 2: People
# ---------------------------------------------------------------------------
with tab_people:
    st.subheader("Indicados com mais indicações")
    top_n = st.slider("Quantidade", 5, 30, 15, key="people_n")
    nom_counts = fdf["name"].value_counts().head(top_n).sort_values()
    fig = go.Figure(go.Bar(
        x=nom_counts.values, y=nom_counts.index, orientation="h", marker_color=BLUE,
    ))
    st.plotly_chart(styled_fig(fig, height=max(320, top_n * 26)), use_container_width=True)

    st.subheader("Indicados com mais vitórias")
    win_counts = (
        fdf[fdf["winner"]]["name"].value_counts().head(top_n).sort_values()
    )
    fig = go.Figure(go.Bar(
        x=win_counts.values, y=win_counts.index, orientation="h", marker_color=ORANGE,
    ))
    st.plotly_chart(styled_fig(fig, height=max(320, top_n * 26)), use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 3: Films
# ---------------------------------------------------------------------------
with tab_films:
    st.subheader("Filmes com mais indicações")
    top_n_f = st.slider("Quantidade", 5, 30, 15, key="films_n")
    film_nom = fdf["film"].value_counts().head(top_n_f).sort_values()
    fig = go.Figure(go.Bar(
        x=film_nom.values, y=film_nom.index, orientation="h", marker_color=AQUA,
    ))
    st.plotly_chart(styled_fig(fig, height=max(320, top_n_f * 26)), use_container_width=True)

    st.subheader("Filmes com mais vitórias")
    film_win = fdf[fdf["winner"]]["film"].value_counts().head(top_n_f).sort_values()
    fig = go.Figure(go.Bar(
        x=film_win.values, y=film_win.index, orientation="h", marker_color=GREEN,
    ))
    st.plotly_chart(styled_fig(fig, height=max(320, top_n_f * 26)), use_container_width=True)

# ---------------------------------------------------------------------------
# Tab 4: Data explorer
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Dados filtrados")
    st.dataframe(
        fdf.sort_values(["year_ceremony", "canon_category"])[
            ["year_ceremony", "canon_category", "name", "film", "winner"]
        ],
        use_container_width=True,
        height=520,
    )
    st.download_button(
        "Baixar CSV filtrado",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="oscar_filtrado.csv",
        mime="text/csv",
    )
