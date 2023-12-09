#include <iostream>
#include <cstdlib>
#include <string>
#include <SDL2/SDL.h>
#include <SDL2/SDL_ttf.h>
#include <SDL2/SDL_image.h>
#include <memory>
#include <array>
#include <vector>
#include <fstream>
#include "graphics-lib/include.h"
#include "json/single_include/nlohmann/json.hpp"

#define SCREEN_WIDTH 1000
#define SCREEN_HEIGHT 800

using json = nlohmann::json;
using namespace std;

bool running = true;

string dir = "";
vector<string> dir_history;
json file_data;
win_data wdata;

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

class file_element {
    public:

    file_element(int pos_x, int pos_y, string name, string type, string id, win_data wdata) {
        this->pos[0] = pos_x;
        this->pos[1] = pos_y;
        this->name = name;
        this->type = type;
        this->id = id;
        this->color = {0, 0, 0, 255};

        if (this->type == "DocumentType") {
            SDL_Surface* surf = IMG_Load("../imgs/file.png");
            this->texture = SDL_CreateTextureFromSurface(wdata.renderer, surf);
            SDL_FreeSurface(surf);
        }
        else if (this->type == "CollectionType") {
            SDL_Surface* surf = IMG_Load("../imgs/folder.png");
            this->texture = SDL_CreateTextureFromSurface(wdata.renderer, surf);
            SDL_FreeSurface(surf);
        }
    }

    void draw(win_data wdata) {
        drawText(wdata.renderer, name.c_str(), this->pos[0], this->pos[1], this->color, 20, "../default-font.ttf");
        SDL_Rect dest = {this->pos[0] - 30, this->pos[1], 25, 25};
        SDL_RenderCopy(wdata.renderer, this->texture, NULL, &dest);
    }

    void click(int posx, int posy, string &dir) {
        if (this->type == "CollectionType") {
            if (posx > this->pos[0] - 30 and posx < this->pos[0] - 5) {
                if (posy > this->pos[1] and posy < this->pos[1] + 25) {
                    //cout << this->name << " " << this->id << " " << dir << endl;
                    dir = this->id;
                }
            }
        }

    }

    private:
    int pos[2];
    string name;
    string type;
    string id;
    SDL_Texture *texture;
    SDL_Color color;
};

vector<file_element> get_elements(win_data wdata, json data, string current_dir, int x_off = 0, int y_off = 0, int max_x = SCREEN_WIDTH, int max_y = SCREEN_HEIGHT, int interval_y = 50, int interval_x = 400) {
    vector<file_element> out;

    int x = 0;
    int y = 0;

    for (const auto &item: data) {
        if (item["parent"] == current_dir) {            
            file_element t(x + x_off, y + y_off, item["visibleName"], item["type"], item["id"], wdata);
            out.push_back(t);

            y += interval_y;

            if (y >= max_y) {
                y = 0;
                x += interval_x;
            }

            if (x >= max_x) break;
        }
    }
    return out;
}

void Draw(win_data wdata, vector<file_element> elements, vector<Button> buttons);

void HandleEvents(vector<file_element> elements, vector<Button> buttons, string &dir);

void HomeDir() {
    dir = "";
}

vector<file_element> elements;

void BackDir() {
    if (dir_history.size() < 2) return;

    dir = dir_history[dir_history.size() - 2];

    auto iter = dir_history.end() - 1;
    dir_history.erase(iter);

    elements = get_elements(wdata, file_data, dir, 50, 10);
}

int main() {
    init(&wdata, SCREEN_HEIGHT, SCREEN_WIDTH);

    //td::string pythonCommand = "time python3 ../../driver/driver.py --ip 192.168.217.1 -l";
    //cout << run_cmd(pythonCommand.c_str()) << endl;

    //cout << "directory: " << run_cmd("pwd") << endl;
    //cout << run_cmd("ls .. | grep default") << endl;

    dir_history.push_back("");

    file_data = load_file("../dump.json");

    elements = get_elements(wdata, file_data, "", 50, 10);

    vector<Button> buttons;

    Button home(1430 - 500 + 15, 10, 0, 0, "HOME");
    home.onClick_func = &HomeDir;
    buttons.push_back(home);

    Button back(1380 - 500 + 15, 10, 0, 0, "BACK");
    back.onClick_func = &BackDir;
    buttons.push_back(back);


    while (running) {
        HandleEvents(elements, buttons, dir);

        SDL_SetRenderDrawColor(wdata.renderer, 170, 170, 170, 255);
        SDL_RenderClear(wdata.renderer);

        Draw(wdata, elements, buttons);

        SDL_RenderPresent(wdata.renderer);

        if (dir != dir_history.back()) {
            elements = get_elements(wdata, file_data, dir, 50, 10);
            dir_history.push_back(dir);
        }
    }

    return 0;
}

void Draw(win_data wdata, vector<file_element> elements, vector<Button> buttons) {
    for (auto &el: elements)    el.draw(wdata);
    for (auto &button: buttons)    button.draw(wdata.renderer);
    return;
}

void HandleEvents(vector<file_element> elements,vector<Button> buttons, string &dir) {
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_QUIT)     running =  false;

        if (event.type == SDL_MOUSEBUTTONDOWN) {
                if (event.button.button == SDL_BUTTON_LEFT) {
                    int mouseX = event.button.x;
                    int mouseY = event.button.y;
                    for (auto &el: elements) el.click(mouseX, mouseY, dir);
                    for (auto &el: buttons) el.checkClick(mouseX, mouseY);
                }
            }

         if (event.type == SDL_MOUSEMOTION) {
                int mouseX = event.motion.x;
                int mouseY = event.motion.y;
                for (auto &button: buttons) button.checkSelect(mouseX, mouseY);
            }
    }
}

