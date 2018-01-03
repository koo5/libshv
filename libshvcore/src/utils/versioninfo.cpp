#include "versioninfo.h"

#include "../core/string.h"

namespace shv {
namespace core {
namespace utils {

VersionInfo::VersionInfo(int major, int minor, int patch, const std::string &branch)
	: m_majorNumber(major)
	, m_minorNumber(minor)
	, m_patchNumber(patch)
	, m_branch(branch)
{
}

VersionInfo::VersionInfo(const std::string &version, const std::string &branch)
	: m_branch(branch)
{
	std::vector<std::string> parts = String::split(version, '.');
	while (parts.size() < 3) {
		parts.push_back("0");
	}
	m_majorNumber = std::stoi(parts[0]);
	m_minorNumber = std::stoi(parts[1]);
	m_patchNumber = std::stoi(parts[2]);
}

std::string VersionInfo::toString() const
{
	return std::to_string(m_majorNumber) + '.' + std::to_string(m_minorNumber) + '.' + std::to_string(m_patchNumber);
}

int VersionInfo::toInt() const
{
	return m_majorNumber * 10000 + m_minorNumber * 100 + m_patchNumber;
}

bool VersionInfo::operator==(const VersionInfo &v) const
{
	return m_majorNumber == v.m_majorNumber && m_minorNumber == v.m_minorNumber && m_patchNumber == v.m_patchNumber && m_branch == v.m_branch;
}

const std::string &VersionInfo::branch() const
{
	return m_branch;
}

int VersionInfo::majorNumber() const
{
	return m_majorNumber;
}

int VersionInfo::minorNumber() const
{
	return m_minorNumber;
}

int VersionInfo::patchNumber() const
{
	return m_patchNumber;
}

}
}
}
