PWN_HOSTNAME=pwnagotchi
PWN_VERSION=master

all: clean install image

install:
	curl https://releases.hashicorp.com/packer/1.4.5/packer_1.4.5_linux_amd64.zip -o /tmp/packer.zip
	unzip /tmp/packer.zip -d /tmp
	sudo mv /tmp/packer /usr/bin/packer
	git clone https://github.com/solo-io/packer-builder-arm-image /tmp/packer-builder-arm-image
	cd /tmp/packer-builder-arm-image && go get -d ./... && go build
	sudo cp /tmp/packer-builder-arm-image/packer-builder-arm-image /usr/bin

image:
	echo "Building image for $(PWN_HOSTNAME) @ $(PWN_VERSION)"
	cd builder && sudo /usr/bin/packer build -var "pwn_hostname=$(PWN_HOSTNAME)" -var "pwn_version=$(PWN_VERSION)" pwnagotchi.json
	sudo apt-get install -y zerofree
	sudo device="$(losetup --partscan --show --find builder/output-pwnagotchi/image)"
	sudo zerofree "${device}p2"
	sudo losetup --detach "$device"
	sudo mv builder/output-pwnagotchi/image pwnagotchi-raspbian-lite-$(PWN_VERSION).img
	sudo sha256sum pwnagotchi-raspbian-lite-$(PWN_VERSION).img > pwnagotchi-raspbian-lite-$(PWN_VERSION).sha256
	sudo zip pwnagotchi-raspbian-lite-$(PWN_VERSION).zip pwnagotchi-raspbian-lite-$(PWN_VERSION).sha256 pwnagotchi-raspbian-lite-$(PWN_VERSION).img

clean:
	rm -rf /tmp/packer-builder-arm-image
	rm -f pwnagotchi-raspbian-lite-*.zip pwnagotchi-raspbian-lite-*.img pwnagotchi-raspbian-lite-*.sha256
	rm -rf builder/output-pwnagotchi  builder/packer_cache
