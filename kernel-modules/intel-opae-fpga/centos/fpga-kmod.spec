%if "%{?_tis_build_type}" == "rt"
%define bt_ext -rt
%else
%undefine bt_ext
%endif

# Define the kmod package name here.
%define kmod_name opae-intel-fpga-driver
# If a release doesn't have an iteration number, just use 0
%define iteration 6

Name:    %{kmod_name}-kmod%{?bt_ext}
Version: 2.0.1
Release: %{iteration}%{?_tis_dist}.%{tis_patch_ver}
Group:   System Environment/Kernel
License: GPLv2
Summary: %{kmod_name}%{?bt_ext} kernel module(s)
URL:     http://www.intel.com/

BuildRequires: kernel%{?bt_ext}-devel, redhat-rpm-config, perl, openssl, elfutils-libelf-devel
ExclusiveArch: x86_64

# Sources.
# The source tarball name may or may not include the iteration number.
Source0:  %{kmod_name}-%{version}.tar.gz
Patch01:  Remove-regmap-mmio-as-it-is-built-into-the-kernel.patch
Patch02:  Fix-compile-error-with-CentOS-8.1-4.18.0-147-kernel.patch
Patch03:  Fix-wrong-kernel-version.patch

%define kversion %(rpm -q kernel%{?bt_ext}-devel | sort --version-sort | tail -1 | sed 's/kernel%{?bt_ext}-devel-//')

%package       -n kmod-opae-fpga-driver%{?bt_ext}
Summary:          OPAE fpga driver kernel module(s)
Group:            System Environment/Kernel
%global _use_internal_dependency_generator 0
Provides:         kernel-modules >= %{kversion}
Provides:         opae-intel-fpga-driver-kmod = %{?epoch:%{epoch}:}%{version}-%{release}
Requires(post):   /usr/sbin/depmod
Requires(postun): /usr/sbin/depmod

%description   -n kmod-opae-fpga-driver%{?bt_ext}
This package provides the opae-fpga-driver kernel module(s) built
for the Linux kernel using the %{_target_cpu} family of processors.

%post          -n kmod-opae-fpga-driver%{?bt_ext}
echo "Working. This may take some time ..."
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(find /lib/modules/%{kversion}/extra/opae-intel-fpga-driver | grep '\.ko$') )
if [ -x "/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /sbin/weak-modules --add-modules
fi
echo "Done."

%preun         -n kmod-opae-fpga-driver%{?bt_ext}
rpm -ql kmod-opae-fpga-driver%{?bt_ext}-%{version}-%{release}.x86_64 | grep '\.ko$' > /var/run/rpm-kmod-opae-fpga-driver%{?bt_ext}-modules

%postun        -n kmod-opae-fpga-driver%{?bt_ext}
echo "Working. This may take some time ..."
if [ -e "/boot/System.map-%{kversion}" ]; then
    /usr/sbin/depmod -aeF "/boot/System.map-%{kversion}" "%{kversion}" > /dev/null || :
fi
modules=( $(cat /var/run/rpm-kmod-opae-fpga-driver%{?bt_ext}-modules) )
rm /var/run/rpm-kmod-opae-fpga-driver%{?bt_ext}-modules
if [ -x "/sbin/weak-modules" ]; then
    printf '%s\n' "${modules[@]}" | /sbin/weak-modules --remove-modules
fi
echo "Done."

%files         -n kmod-opae-fpga-driver%{?bt_ext}
%defattr(644,root,root,755)
/lib/modules/%{kversion}/
%config(noreplace)/etc/depmod.d/kmod-opae-intel-fpga-driver.conf
%doc /usr/share/doc/kmod-%{kmod_name}-%{version}/

# Disable the building of the debug package(s).
%define debug_package %{nil}

%description
This package provides the %{kmod_name} kernel module(s).
It is built to depend upon the specific ABI provided by a range of releases
of the same variant of the Linux kernel and not on any one specific build.

%prep
%autosetup -p 1 -n %{kmod_name}-%{version}
echo "override %{kmod_name} * weak-updates/%{kmod_name}" > kmod-%{kmod_name}.conf

%build
%{__make} KERNELDIR=%{_usrsrc}/kernels/%{kversion}

%install
%{__install} -d %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} %{_builddir}/%{kmod_name}-%{version}/*.ko %{buildroot}/lib/modules/%{kversion}/extra/%{kmod_name}/
%{__install} -d %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} kmod-%{kmod_name}.conf %{buildroot}%{_sysconfdir}/depmod.d/
%{__install} -d %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} COPYING %{buildroot}%{_defaultdocdir}/kmod-%{kmod_name}-%{version}/
%{__install} -d %{buildroot}%{_sysconfdir}/modules-load.d

# Strip the modules(s).
find %{buildroot} -type f -name \*.ko -exec %{__strip} --strip-debug \{\} \;

# Always Sign the modules(s).
# If the module signing keys are not defined, define them here.
%{!?privkey: %define privkey /usr/src/kernels/%{kversion}/signing_key.pem}
%{!?pubkey: %define pubkey /usr/src/kernels/%{kversion}/signing_key.x509}
for module in $(find %{buildroot} -type f -name \*.ko);
do /usr/src/kernels/%{kversion}/scripts/sign-file \
    sha256 %{privkey} %{pubkey} $module;
done

%clean
%{__rm} -rf %{buildroot}

%changelog
* Thu Feb 11 2016 Matthias Saou <matthias@saou.eu> 1.4.25-1
- Initial RPM package, based on elrepo.org's ixgbe one.
