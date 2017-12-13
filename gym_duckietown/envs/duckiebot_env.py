#!/usr/bin/env python
import rospy
from transfer_learning.DuckiebotGymEnv import DuckiebotEnv
from duckietown_utils.image_rescaling import d8_image_resize_no_interpolation
from duckietown_utils.image_conversions import rgb_from_imgmsg
from duckietown_msgs.msg import Twist2DStamped, Image





class DuckiebotEnv(gym.Env):
    """An environment that is the actual real robot """

    rospy.init_node("transfer_learning", anonymous=True)
    image_grabber = ImageGrabber()
    sub_image = rospy.Subscriber("~image_rect", Image, cbImage, queue_size=1,tcp_nodelay=True)
    pub_cmd   = rospy.Publisher("~wheels_cmd", WheelCmdStamped, queue_size=1)

    metadata = {
        'render.modes': ['human', 'rgb_array', 'app'],
        'video.frames_per_second' : 30
    }

    
    def __init__(self):
        # Two-tuple of wheel torques, each in the range [-1, 1]
        self.action_space = spaces.Box(
            low=-1,
            high=1,
            shape=(2,)
        )

        # We observe an RGB image with pixels in [0, 255]
        self.observation_space = spaces.Box(
            low=0,
            high=1,
            shape=IMG_SHAPE
        )

        self.reward_range = (-1, 1000)

        # Environment configuration
        self.maxSteps = 50

        # Array to render the image into
        self.imgArray = np.zeros(shape=IMG_SHAPE, dtype=np.float32)

        # For rendering
        self.window = None

        # We continually stream in images and then just take the latest one.
        self.latest_img = None
        
        # For displaying text
        self.textLabel = pyglet.text.Label(
            font_name="Arial",
            font_size=14,
            x = 5,
            y = WINDOW_SIZE - 19
        )


        # Initialize the state
        self.seed()
        self.reset()

    def cbImage(self, msg):
        self.last_good_img = rgb_from_imgmsg(msg)

                
    def _close(self):
        pass

    def _reset(self):
        # Step count since episode start
        self.stepCount = 0
        obs = self._renderObs()

        # Return first observation
        return obs

    def _seed(self, seed=None):
        self.np_random, _ = seeding.np_random(seed)

        return [seed]


    def _step(self, action):

        # we don't care about this reward since we're not training..
        reward = 0
        # don't worry about episodes blah blah blah we will just shut down the robot when we're done
        done = False

            # 
# 1. execute action
        wheels_cmd_msg = Twist2DStamped()
        wheels_cmd_msg.vel_right = action[0]
        wheels_cmd_msg.vel_left = action[1]
        self.pub_cmd.publish(wheels_cmd_msg)

# 2. grab result image
        obs = self._renderObs()

# 3. return image as "obs"

        self.stepCount += 1
            
        return obs, reward, done, {}

    def _renderObs(self):
        return d8_image_resize_no_interpolation(image_grabber.last_good_img,[64,64])
        # return a camera frame

        return self.latest_img

    def _render(self, mode='human', close=False):
        if close:
            if self.window:
                self.window.close()
            return

        # Render the observation
        img = self._renderObs()

        if mode == 'rgb_array':
            return img

        if self.window is None:
            context = pyglet.gl.get_current_context()
            self.window = pyglet.window.Window(
                width=WINDOW_SIZE,
                height=WINDOW_SIZE
            )

        self.window.switch_to()
        self.window.dispatch_events()

        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        glViewport(0, 0, WINDOW_SIZE, WINDOW_SIZE)

        self.window.clear()

        # Setup orghogonal projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glOrtho(0, WINDOW_SIZE, 0, WINDOW_SIZE, 0, 10)

        # Draw the image to the rendering window
        width = img.shape[0]
        height = img.shape[1]
        img = np.uint8(img * 255)
        imgData = pyglet.image.ImageData(
            width,
            height,
            'RGB',
            img.tobytes(),
            pitch = width * 3,
        )
        imgData.blit(0, 0, 0, WINDOW_SIZE, WINDOW_SIZE)

        # Display position/state information
        pos = self.curPos
        self.textLabel.text = "(%.2f, %.2f, %.2f)" % (pos[0], pos[1], pos[2])
        self.textLabel.draw()

        if mode == 'human':
            self.window.flip()

        






        


