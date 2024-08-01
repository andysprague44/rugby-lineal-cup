
# Lineal Cup for rugby sevens

The idea is to track the current holder of the "rugby lineal cup". The holder remains the holder until they loose to another team in any competition, at which point the winner of that game is the new holder.

Inspired by an instagram channel @raeburnshield, where this is tracked for the international mens game manually. 

For rugby sevens, the volume of games means we needs data to track due to the volume of games, hence this project!

## Getting started

In the `lineal_cup` directory, copy `.env.example` to `.env` and add your `SPORT_RADAR_API_KEY`

Change to `load=True` in the block `if __name__ == "__main__"`

Run
```sh
python -m lineal_cup.app
```

You can now switch back to `load=False`, to iterate without hitting the API.


## How far back?

Starting from the Sportradar API data means the cups starts in 2016, there is no data futher back. Know where to get historic data? Let me know!

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Contact

<andy.sprague44@gmail.com>
