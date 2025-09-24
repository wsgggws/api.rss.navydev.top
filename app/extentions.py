from fastapi_radar import Radar


def setup_extentions(app):
    # fastapi_radar, 没有使用同步引擎，不 enable db_engine
    radar = Radar(app)
    radar.create_tables()
