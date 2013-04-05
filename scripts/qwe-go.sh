# NOTE Must be run as root
GPIO_WAIT_CMD="/home/user/code/high-level/etc/gpio.o 113" # NOTE uses absolute path
QWE_DIR="/home/user/code/high-level/qwe" # where can we find controller?
CONTROLLER=${1:-controller.py}

PWD=`pwd`

# Remove Kernel module that might eat up GPIO pins
echo "qwe-go: Removing Kernel module..."
rmmod gpio_keys  # TODO check if it is even loaded?

# TODO check if gpio.o exists in the right place, if not make it

# Wait for GPIO button press
echo "qwe-go: Waiting for GPIO button press..."
eval $GPIO_WAIT_CMD

# Launch controller
echo "qwe-go: Changing to ${QWE_DIR}..."
cd $QWE_DIR
echo "qwe-go: Launching ${CONTROLLER}..."
python $CONTROLLER

echo "qwe-go: Done!"
echo "qwe-go: Changing back to ${PWD}..."
cd $PWD
