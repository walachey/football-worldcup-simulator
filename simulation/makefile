CPP_FILES := $(wildcard *.cpp) $(wildcard deps/json_spirit/*.cpp)
OBJ_FILES := $(addprefix obj/,$(notdir $(CPP_FILES:.cpp=.o)))
LD_FLAGS := 
LD_LIBS := -Wl,--no-as-needed -pthread
CC_FLAGS := -std=c++11 -I deps -pthread


ifdef DEBUG
#	$(info Debug enabled..)
	CC_FLAGS += -g 
else
#	$(info no debug)
	CC_FLAGS += -DNDEBUG -O3
endif

simulator: $(OBJ_FILES)
	g++ $(LD_FLAGS) -o $@ $^ $(LD_LIBS) 
	
ifdef MOVE
	@echo "Moving simulator to worker directory.."
	mv simulator ../worker/simulator
endif

obj/%.o: %.cpp
	g++ -c -o $@ $< $(CC_FLAGS)

obj/%.o: deps/json_spirit/%.cpp
	g++ -c -o $@ $< $(CC_FLAGS)

clean:
	-rm -rf obj/*.o
	
#-include $(OBJFILES:.o=.d)
