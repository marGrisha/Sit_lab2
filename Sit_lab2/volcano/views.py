from django.shortcuts import render
from django.db.models import Count, Sum, Max
from django.db.models.functions import Coalesce

from .models import Country, Location, Volcano, Eruption, Impact


def index(request):
    totals = {
        "countries": Country.objects.count(),
        "locations": Location.objects.count(),
        "volcanoes": Volcano.objects.count(),
        "eruptions": Eruption.objects.count(),
        "impacts": Impact.objects.count(),
    }

    # --- Таблицы "как отношения БД" ---

    # Country table (все страны)
    countries_qs = Country.objects.order_by("name")
    country_rows = [[c.id, c.name] for c in countries_qs]

    # Location table (все локации)
    locations_qs = Location.objects.select_related("country").order_by("country__name", "name")
    location_rows = [[l.id, l.country.name, l.name] for l in locations_qs]

    # Volcano table (все вулканы)
    volcanoes_qs = Volcano.objects.select_related("location__country").order_by(
        "location__country__name", "location__name", "name"
    )
    volcano_rows = [
        [
            v.id,
            v.location.country.name,
            v.location.name,
            v.name,
            v.latitude,
            v.longitude,
            v.elevation_m,
            v.volcano_type,
            v.status,
        ]
        for v in volcanoes_qs
    ]

    # Eruption table (последние 50, чтобы страница не была огромной)
    eruptions_qs = (
        Eruption.objects
        .select_related("volcano__location__country")
        .order_by("-year", "-month", "-day")[:50]
    )
    eruption_rows = [
        [
            e.id,
            e.volcano.location.country.name,
            e.volcano.location.name,
            e.volcano.name,
            e.year, e.month, e.day,
            "TSU" if e.tsu_flag else "",
            "EQ" if e.eq_flag else "",
            e.time_code,
            e.vei,
            e.agent,
        ]
        for e in eruptions_qs
    ]

    # Impact table (последние 50)
    impacts_qs = (
        Impact.objects
        .select_related("eruption__volcano__location__country")
        .order_by("-eruption__year", "-eruption__month", "-eruption__day")[:50]
    )
    impact_rows = [
        [
            im.id,
            im.eruption.volcano.location.country.name,
            im.eruption.volcano.name,
            im.eruption.year, im.eruption.month, im.eruption.day,
            im.total_deaths,
            im.total_injuries,
            im.total_missing,
            im.total_damage_musd,
            im.total_houses_destroyed,
        ]
        for im in impacts_qs
    ]

    # --- Статистика (агрегации) ---

    # 1) Топ стран по числу извержений + max VEI + сумма смертей
    top_countries_qs = (
        Country.objects
        .annotate(
            eruptions_count=Count("locations__volcanoes__eruptions", distinct=True),
            volcanoes_count=Count("locations__volcanoes", distinct=True),
            max_vei=Max("locations__volcanoes__eruptions__vei"),
            total_deaths_sum=Coalesce(Sum("locations__volcanoes__eruptions__impact__total_deaths"), 0),
        )
        .order_by("-eruptions_count", "name")[:15]
    )
    top_country_rows = [
        [c.name, c.volcanoes_count, c.eruptions_count, c.max_vei, c.total_deaths_sum]
        for c in top_countries_qs
    ]

    # 2) Распределение VEI
    vei_stats_qs = (
        Eruption.objects
        .values("vei")
        .annotate(cnt=Count("id"))
        .order_by("vei")
    )
    vei_rows = [[x["vei"], x["cnt"]] for x in vei_stats_qs]

    # 3) Топ вулканов по числу извержений
    top_volcanoes_qs = (
        Volcano.objects
        .select_related("location__country")
        .annotate(eruptions_count=Count("eruptions"), max_vei=Max("eruptions__vei"))
        .order_by("-eruptions_count")[:15]
    )
    top_volcano_rows = [
        [v.location.country.name, v.name, v.eruptions_count, v.max_vei]
        for v in top_volcanoes_qs
    ]

    # 4) Сколько извержений с TSU/EQ
    tsu_count = Eruption.objects.filter(tsu_flag=True).count()
    eq_count = Eruption.objects.filter(eq_flag=True).count()

    return render(
        request,
        "index.html",
        {
            "totals": totals,
            "country_rows": country_rows,
            "location_rows": location_rows,
            "volcano_rows": volcano_rows,
            "eruption_rows": eruption_rows,
            "impact_rows": impact_rows,
            "top_country_rows": top_country_rows,
            "vei_rows": vei_rows,
            "top_volcano_rows": top_volcano_rows,
            "tsu_count": tsu_count,
            "eq_count": eq_count,
        },
        using="jinja2",
    )