import config
import logging
import version


def main():
    try:
        logging.basicConfig(level=logging.DEBUG)
        logging.info('This is %s v%s' % (version.PRODUCT, version.VERSION))
        cfg = config.Config()
    finally:
        logging.info('Done')


if __name__ == '__main__':
    main()
