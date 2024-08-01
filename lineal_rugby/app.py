from collections import Counter
import requests
import time
import json
from typing import Tuple
from .models import *
from .config import Config

config = Config()


def get_json(url):
    response = requests.request("GET", url + f"?api_key={config.SPORT_RADAR_API_KEY}")
    response.raise_for_status()
    time.sleep(2)  # avoid rate limiting
    return response.json()


def _to_lineal_cup_event(summary: Summary) -> LinealCupEvent:
    """Get all the info we need for tracking lineal cup holder"""
    winner_id = summary.sport_event_status.winner_id
    if winner_id:
        winner = [c for c in summary.sport_event.competitors if c.id == winner_id][0]
        looser = [c for c in summary.sport_event.competitors if c.id != winner_id][0]
    else:
        # match tied
        winner = summary.sport_event.competitors[0]
        looser = summary.sport_event.competitors[1]

    return LinealCupEvent(
        start_time=summary.sport_event.start_time,
        winner_name=winner.name,
        loser_name=looser.name,
        is_tie=(winner_id is None),
        gender=summary.sport_event.sport_event_context.competition.gender,
        competition_name=summary.sport_event.sport_event_context.competition.name,
    )


def _get_rugby_sevens_sportradar_data() -> SportRadarData:
    base_url = "https://api.sportradar.com/rugby-sevens/trial/v3/en"
    competitions = get_json(f"{base_url}/competitions.json")
    competitions = Competitions(**competitions).competitions

    seasons_json = get_json(f"{base_url}/seasons.json")
    seasons = Seasons(**seasons_json).seasons

    data = SportRadarData()

    for season in seasons:
        print("Running season:", season.name)
        season_summary_json = get_json(f"{base_url}/seasons/{season.id}/summaries.json")
        season_summary = SeasonSummary(**season_summary_json)
        season_summary.season = season
        season_summary.competition = next(
            comp for comp in competitions if comp.id == season.competition_id
        )
        data.season_summaries.append(season_summary)

    with open("data/sportradar_data.json", "w") as file:
        file.write(data.model_dump_json(indent=4))

    return data


def _to_lineal_cups(
    data: SportRadarData,
) -> Tuple[LinealCup, LinealCup]:
    """Return 2 lineal cup models, 1 for men, one for women"""
    season_summaries = []
    for season_summary in data.season_summaries:
        season_summaries += season_summary.summaries

    events: List[LinealCupEvent] = []

    events += [
        _to_lineal_cup_event(summary)
        for summary in season_summaries
        # completed matches only
        if summary.sport_event_status.match_status == "ended"
        # internationals only
        and summary.sport_event.competitors[0].country is not None
    ]

    events.sort(key=lambda event: event.start_time)

    men_sevens_events = [event for event in events if event.gender == "men"]
    if men_sevens_events:
        men_sevens_lineal_cup = LinealCup(
            competition_name=men_sevens_events[0].competition_name,
            gender=men_sevens_events[0].gender,
            events=men_sevens_events,
        )
        with open("data/men_lineal_cup.json", "w") as file:
            file.write(men_sevens_lineal_cup.model_dump_json(indent=4))

    women_sevens_events = [event for event in events if event.gender != "men"]
    if women_sevens_events:
        womens_sevens_lineal_cup = LinealCup(
            competition_name=women_sevens_events[0].competition_name,
            gender=women_sevens_events[0].gender,
            events=women_sevens_events,
        )
        with open("data/women_lineal_cup.json", "w") as file:
            file.write(womens_sevens_lineal_cup.model_dump_json(indent=4))

    return men_sevens_lineal_cup, womens_sevens_lineal_cup


def augment_cup_holders(model: LinealCup) -> None:
    events = model.events
    events.sort(key=lambda event: event.start_time)

    current_holder = None
    model.holders = LinearCupHolders()
    model.holders.holders = []

    for event in events:
        if current_holder is None and event.is_tie:
            # first event is a tie, no holder yet
            current_holder = None

        elif current_holder is None:
            # first event
            current_holder = event.winner_name
            model.holders.holders.append(
                LinearCupHolder(start_time=event.start_time, holder=current_holder)
            )

        elif event.winner_name == current_holder or event.loser_name == current_holder:
            if not event.is_tie:
                current_holder = event.winner_name
            # else current_holder remains the same

            # still want to append the event if it's a tie, as the holder gets another 'point'
            model.holders.holders.append(
                LinearCupHolder(start_time=event.start_time, holder=current_holder)
            )

        # else ignore any game *not* involving the current holder

    model.current_holder = current_holder

    with open(f"data/{model.gender}_lineal_cup_holders.json", "w") as file:
        file.write(model.holders.model_dump_json(indent=4))


def augment_cup_stats(model: LinealCup) -> None:
    holder_names = [x.holder for x in model.holders.holders]
    holder_counts = dict(
        sorted(
            Counter(holder_names).items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )
    model.statistics = LinealCupStatistics(wins_by_country=holder_counts)

    with open(f"data/{model.gender}_lineal_cup_stats.json", "w") as file:
        file.write(model.statistics.model_dump_json(indent=4))


def main(load=False):
    if load:
        data = _get_rugby_sevens_sportradar_data()

    else:
        with open("data/sportradar_data.json", "r") as file:
            data = SportRadarData(**json.load(file))

    men_sevens_lineal_cup, womens_sevens_lineal_cup = _to_lineal_cups(data)

    augment_cup_holders(womens_sevens_lineal_cup)
    augment_cup_holders(men_sevens_lineal_cup)

    augment_cup_stats(womens_sevens_lineal_cup)
    augment_cup_stats(men_sevens_lineal_cup)

    print("Done!")


if __name__ == "__main__":
    main(load=True)
