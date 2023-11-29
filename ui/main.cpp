#include <iostream>
#include <cstdlib>
#include <string>
#include <SDL2/SDL.h>
#include <memory>
#include <array>
#include <fstream>
#include "graphics-lib/include.h"
#include "json/single_include/nlohmann/json.hpp"

using json = nlohmann::json;
using namespace std;

void Draw();
void HandleEvents();
bool running = true;

string run_cmd(const char* cmd) {
    string out;     // stores value to be returned
    array<char,128> buffer;     // stores temporarely part of the return value. Used to read cmd output in chunks
    unique_ptr<FILE,decltype(&pclose)> pipe(popen(cmd, "r"), pclose);   // a smart pointer to store a pointer to the FILE object opened by popen to represent the output of the command

    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr)  out += buffer.data();   // reads from the stream in chunks, untill eof is reached. Chunks are then appendend to the output string

    return out;
}

json load_file(const char* filepath) {
    ifstream file(filepath);

    if (!file.is_open()) {
            throw std::runtime_error("Unable to open file");
        }

    json out;
    file >> out;
    return out;
}

int main() {
    win_data wdata;
    init(&wdata, 500, 1000);

    //td::string pythonCommand = "time python3 ../../driver/driver.py --ip 192.168.217.1 -l";
    //cout << run_cmd(pythonCommand.c_str()) << endl;

    json file_data = load_file("../dump.json");

    while (running) {
        HandleEvents();

        SDL_SetRenderDrawColor(wdata.renderer, 170, 170, 170, 255);
        SDL_RenderClear(wdata.renderer);

        Draw();

        SDL_RenderPresent(wdata.renderer);
    }

    return 0;
}

void Draw() {
    return;
}

void HandleEvents() {
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_QUIT)     running =  false;
    }
}
