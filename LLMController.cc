
#ifdef _WIN32
#  undef _WIN32_WINNT
#  define _WIN32_WINNT 0x0A00  // Windows 10
#endif

#include "LLMController.h"
#include "veins/modules/mobility/traci/TraCICommandInterface.h"

#include "veins/ext/httplib/httplib.h"
#include "veins/ext/json/json.hpp"

using json = nlohmann::json;
Define_Module(LLMController);

void LLMController::initialize(int stage) {
    TraCIDemo11p::initialize(stage);

    if (stage == 0) {
        EV << "LLMController initialized\n";
    }
}

void LLMController::handleSelfMsg(cMessage* msg) {
    std::string sumoId = mobility->getExternalId();

    if (sumoId == "accidentCar") {
        traciVehicle->setSpeed(0);
        EV_WARN << "[ACCIDENT] accidentCar este oprit permanent!\n";
        TraCIDemo11p::handleSelfMsg(msg);
        return;
    }

    auto speed = mobility->getSpeed();
    auto pos = mobility->getPositionAt(simTime());


    // date suplimentare de la TraCI
    std::string laneId   = traciVehicle->getLaneId();
    double      maxSpeed = traciVehicle->getMaxSpeed();

    EV_INFO << "[LLM] handleSelfMsg t=" << simTime()
            << " myId=" << myId
            << " speed=" << speed
            << " pos=(" << pos.x << "," << pos.y << ")"
            << " laneId=" << laneId
            << " maxSpeed=" << maxSpeed
            << "\n";

    json req;
    req["vehicle_id"]  = myId;
    req["time"]        = (double)SIMTIME_DBL(simTime());
    req["speed"]       = speed;
    req["position"]    = { {"x", pos.x}, {"y", pos.y} };
    req["lane_id"]     = laneId;
    req["speed_limit"] = maxSpeed;

    EV_INFO << "[LLM] Trimit cerere HTTP la 127.0.0.1:8000/decide body="
            << req.dump() << "\n";

    try {
        httplib::Client cli("127.0.0.1", 8000);
        cli.set_connection_timeout(1, 0);   // 1 secunda
        cli.set_read_timeout(5, 0);

        auto res = cli.Post("/decide", req.dump(), "application/json");

        if (!res) {
            EV_WARN << "[LLM] NU am primit raspuns de la serverul LLM \n";
        }
        else {
            EV_INFO << "[LLM] Raspuns LLM: status=" << res->status
                    << " body=" << res->body << "\n";

            if (res->status == 200) {
                try {
                    auto resp = json::parse(res->body);

                    double accel = resp.value("accel", 0.0);
                    EV_INFO << "[LLM] accel primit=" << accel << "\n";

                    if (accel < -3.0) accel = -3.0;
                    if (accel >  3.0) accel =  3.0;

                    double newSpeed = speed + accel;
                    if (newSpeed < 0.0) newSpeed = 0.0;
                    if (newSpeed > 30.0) newSpeed = 30.0;

                    EV_INFO << "[LLM] setSpeed from " << speed
                            << " to " << newSpeed << " m/s\n";

                    traciVehicle->setSpeed(newSpeed);
                }
                catch (std::exception& e) {
                    EV_WARN << "[LLM] Eroare la parsarea raspunsului JSON: "
                            << e.what() << "\n";
                }
            }
        }
    }
    catch (std::exception& e) {
        EV_ERROR << "[LLM] Exceptie la HTTP request: " << e.what() << "\n";
    }

    TraCIDemo11p::handleSelfMsg(msg);
}
