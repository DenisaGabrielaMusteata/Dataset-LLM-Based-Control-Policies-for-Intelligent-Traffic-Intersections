

#pragma once

#include "veins/modules/application/traci/TraCIDemo11p.h"

class LLMController : public veins::TraCIDemo11p {
protected:
    virtual void initialize(int stage) override;
    virtual void handleSelfMsg(cMessage* msg) override;
};
