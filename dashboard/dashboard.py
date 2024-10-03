import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime as dt
import folium
from folium import plugins
from streamlit_folium import folium_static

st.set_page_config(page_title="Proyek Analisis Data: E-Commerce Public Dataset", layout="wide")
st.header("E-Commerce Dataset Dashboard :shopping_trolley:")

def create_categories_df(orders_df: pd.DataFrame) -> pd.DataFrame:
    sum_order_items_df = (
        orders_df.groupby("product_category_name")
        .agg(
            {
                "product_id": "count",
            }
        )
        .rename(columns={"product_id": "sold_count"})
    )
    sum_order_items_df.sort_values("sold_count", ascending=False, inplace=True)
    return sum_order_items_df


def create_order_delivery_time_df(
    orders_order_reviews_df: pd.DataFrame,
) -> pd.DataFrame:
    orders_order_reviews_df.dropna(subset=["review_score"], inplace=True)

    order_delivery_time_and_review_df = orders_order_reviews_df[
        ["order_purchase_timestamp", "order_delivered_customer_date", "review_score"]
    ]
    order_delivery_time_and_review_df["time_between_purchase_and_delivery_days"] = (
        order_delivery_time_and_review_df["order_delivered_customer_date"]
        - order_delivery_time_and_review_df["order_purchase_timestamp"]
    ).dt.days

    return (
        order_delivery_time_and_review_df.groupby(
            ["time_between_purchase_and_delivery_days"]
        ).agg({"review_score": "mean"})
    ).reset_index()


def create_heat_data(customer_order_geolocation_df: pd.DataFrame) -> list:
    return customer_order_geolocation_df[
        ["geolocation_lat", "geolocation_lng"]
    ].values.tolist()


def get_heatmap_center(customer_order_geolocation_df: pd.DataFrame) -> list:
    centered_point = customer_order_geolocation_df.agg(
        {"geolocation_lat": "mean", "geolocation_lng": "mean"}
    )
    return centered_point.to_list()

@st.cache_data(show_spinner=False)
def load_data():
    complete_order_df = pd.read_csv("dashboard/complete_order_df.csv")

    customer_geo_df = pd.read_csv("dashboard/geo_customer.csv")
    geo_df = pd.read_csv("dashboard/geo_df.csv")
    orders_geo_df = pd.read_csv("dashboard/geo_orders.csv")

    orders_order_reviews_df = pd.read_csv("dashboard/orders_order_reviews_df.csv")

    complete_order_df.sort_values(by="order_purchase_timestamp", inplace=True)
    complete_order_df.reset_index(inplace=True)

    customer_order_geolocation_df = pd.merge(customer_geo_df, geo_df, left_on="customer_zip_code_prefix", right_on="geolocation_zip_code_prefix")
    customer_order_geolocation_df = pd.merge(customer_order_geolocation_df, orders_geo_df, on="customer_id")

    customer_order_geolocation_df.sort_values(by="order_purchase_timestamp", inplace=True)
    customer_order_geolocation_df.reset_index(inplace=True)

    orders_order_reviews_df.sort_values(by="order_purchase_timestamp", inplace=True)
    orders_order_reviews_df.reset_index(inplace=True)


    complete_order_df["order_purchase_timestamp"] = pd.to_datetime(
        complete_order_df["order_purchase_timestamp"]
    )
    customer_order_geolocation_df["order_purchase_timestamp"] = pd.to_datetime(
        customer_order_geolocation_df["order_purchase_timestamp"]
    )
    orders_order_reviews_df["order_purchase_timestamp"] = pd.to_datetime(
        orders_order_reviews_df["order_purchase_timestamp"]
    )
    orders_order_reviews_df["order_delivered_customer_date"] = pd.to_datetime(
        orders_order_reviews_df["order_delivered_customer_date"]
    )

    return complete_order_df, customer_order_geolocation_df, orders_order_reviews_df
    

# Load cleaned data
with st.spinner("Loading data..."):
    complete_order_df, customer_order_geolocation_df, orders_order_reviews_df = load_data()

# Filter data
min_date = complete_order_df["order_purchase_timestamp"].min()
max_date = complete_order_df["order_purchase_timestamp"].max()


start_date, end_date = st.date_input(
    label="Rentang Waktu",
    min_value=min_date,
    max_value=max_date,
    value=[min_date, max_date],
)

start_date_dt = dt.datetime.combine(start_date, dt.datetime.min.time())
end_date_dt = dt.datetime.combine(end_date, dt.datetime.max.time())

filtered_complete_order_df = complete_order_df[
    (complete_order_df["order_purchase_timestamp"] >= start_date_dt)
    & (complete_order_df["order_purchase_timestamp"] <= end_date_dt)
]
filtered_customer_order_geolocation_df = customer_order_geolocation_df[
    (customer_order_geolocation_df["order_purchase_timestamp"] >= start_date_dt)
    & (customer_order_geolocation_df["order_purchase_timestamp"] <= end_date_dt)
]
filtered_orders_order_reviews_df = orders_order_reviews_df[
    (orders_order_reviews_df["order_purchase_timestamp"] >= start_date_dt)
    & (orders_order_reviews_df["order_purchase_timestamp"] <= end_date_dt)
]

# Menyiapkan berbagai dataframe
categories_df = create_categories_df(filtered_complete_order_df)
order_delivery_time_df = create_order_delivery_time_df(filtered_orders_order_reviews_df)

# Product category performance
st.subheader("Best & Worst Performing Product Categories")

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

sns.barplot(
    x="sold_count",
    y="product_category_name",
    hue="product_category_name",
    data=categories_df.head(5),
    palette=colors,
    ax=ax[0],
)
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Best Performing Category", loc="center", fontsize=15)
ax[0].tick_params(axis="y", labelsize=12)

sns.barplot(
    x="sold_count",
    y="product_category_name",
    hue="product_category_name",
    data=categories_df.tail(5)[::-1],
    palette=colors,
    ax=ax[1],
)
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Worst Performing Category", loc="center", fontsize=15)
ax[1].tick_params(axis="y", labelsize=12)

st.pyplot(fig)

# Delivery time vs review score
st.subheader("Delivery Time vs Review Score")

fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(24, 6))
colors = ["#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#72BCD4"]

sns.regplot(
    x="time_between_purchase_and_delivery_days",
    y="review_score",
    data=order_delivery_time_df,
    ax=ax,
)
ax.set_ylabel("Average Score (out of 5)", fontsize=12)
ax.set_xlabel("Delivery Time (days)", fontsize=12)
ax.tick_params(axis="y", labelsize=12)

st.pyplot(fig)

# Heat map
st.subheader("Heatmap of Order Destinations")
sampling = st.number_input(
    "Sampling",
    min_value=500,
    max_value=100000,
    step=500,
    value=1000,
)

sampled_geo_df = filtered_customer_order_geolocation_df.sample(n=sampling)

heat_data = create_heat_data(sampled_geo_df)
map_center = get_heatmap_center(sampled_geo_df)

folium_map = folium.Map(location=map_center, tiles="OpenStreetMap", zoom_start=7)

plugins.HeatMap(heat_data).add_to(folium_map)

folium_static(folium_map, width=1200, height=600)

st.caption("Made by Nathan Adhitya for Proyek Analisis Data @ Dicoding")
